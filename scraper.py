"""
CTQ Veille - Scraper v2.0 — Flux RSS officiels
Sources: https://www.pes.ctq.gouv.qc.ca/rss/
"""

import requests
import json
import hashlib
import os
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import Optional
import time
import logging
from xml.etree import ElementTree as ET
import urllib3

# Désactiver les warnings SSL (certificat gouvernement Québec)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ctq_scraper")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "fr-CA,fr;q=0.9",
    "Referer": "https://www.ctq.gouv.qc.ca/",
}

# ─── FLUX RSS OFFICIELS CTQ ──────────────────────────────────────────────────
RSS_FEEDS = {
    "autobus": {
        "label": "Avis publics — Autobus",
        "url": "https://www.pes.ctq.gouv.qc.ca/rss/AUTOBUS.xml",
        "icon": "🚌",
        "priority": "haute",
        "section": "avis_publics",
    },
    "courtage": {
        "label": "Avis publics — Courtage",
        "url": "https://www.pes.ctq.gouv.qc.ca/rss/COURTAGE.xml",
        "icon": "📋",
        "priority": "moyenne",
        "section": "avis_publics",
    },
    "ferroviaire": {
        "label": "Avis publics — Ferroviaire",
        "url": "https://www.pes.ctq.gouv.qc.ca/rss/FERROVIAIR.xml",
        "icon": "🚂",
        "priority": "basse",
        "section": "avis_publics",
    },
    "erratum": {
        "label": "Erratum & Corrections",
        "url": "https://www.pes.ctq.gouv.qc.ca/rss/ERRATUM.xml",
        "icon": "🔔",
        "priority": "haute",
        "section": "actualites",
    },
}

# Sections CTQ additionnelles (HTML scraping)
BASE_URL = "https://www.ctq.gouv.qc.ca"
HTML_SECTIONS = {
    "decisions": {
        "label": "Décisions rendues",
        "url": f"{BASE_URL}/services-en-ligne/recherche-de-decisions/",
        "icon": "⚖️",
        "priority": "moyenne",
    },
    "actualites": {
        "label": "Actualités et dossiers prioritaires",
        "url": f"{BASE_URL}/actualites-et-dossiers-prioritaires/",
        "icon": "📢",
        "priority": "moyenne",
    },
    "calendrier": {
        "label": "Calendrier des audiences",
        "url": f"{BASE_URL}/la-commission/laudience/",
        "icon": "🗓️",
        "priority": "haute",
    },
}


@dataclass
class CTQItem:
    section: str
    section_label: str
    icon: str
    priority: str
    title: str
    description: str
    url: str
    date_publie: str
    hash_id: str
    is_new: bool = False
    tags: list = None
    source: str = "rss"

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


def make_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def detect_tags(text: str) -> list:
    text_lower = text.lower()
    tags = []
    keyword_map = {
        "Nouveau permis": ["nouveau permis", "demande de permis", "délivrance"],
        "Transfert": ["transfert", "cession"],
        "Modification territoire": ["territoire", "municipalité", "agglomération", "parcours"],
        "Nolisé": ["nolisé", "nolise", "charte", "charter"],
        "Transport scolaire": ["scolaire", "élèves", "écoliers"],
        "Révocation": ["révocation", "révoqué", "suspension", "annulation"],
        "Interurbain": ["interurbain"],
        "Urbain": ["urbain"],
        "Audience": ["audience", "séance"],
        "Tarification": ["tarif", "indexation"],
        "VFÉ": ["faibles émissions", "électrique", "vfe", "zéro émission"],
        "Erratum": ["erratum", "correction", "rectification"],
        "Courtage": ["courtage", "vrac"],
    }
    for tag, keywords in keyword_map.items():
        if any(k in text_lower for k in keywords):
            tags.append(tag)
    return tags


def parse_rss_date(date_str: str) -> str:
    """Convertit une date RSS (RFC 2822) en format ISO."""
    if not date_str:
        return date.today().isoformat()
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.date().isoformat()
    except Exception:
        return date.today().isoformat()


# ─── RSS SCRAPER ─────────────────────────────────────────────────────────────

def fetch_rss_feed(feed_key: str, feed_config: dict) -> list[CTQItem]:
    """Récupère et parse un flux RSS CTQ."""
    items = []
    url = feed_config["url"]

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        # Visiter la page principale d'abord pour cookies
        try:
            session.get("https://www.ctq.gouv.qc.ca/", timeout=10, verify=False)
        except Exception:
            pass

        resp = session.get(url, timeout=20, verify=False)

        if resp.status_code != 200:
            log.warning(f"RSS {feed_key}: HTTP {resp.status_code}")
            return items

        root = ET.fromstring(resp.content)
        rss_items = root.findall('.//item')

        log.info(f"RSS {feed_key}: {len(rss_items)} items trouvés")

        for rss_item in rss_items:
            title = (rss_item.findtext('title') or '').strip()
            description = (rss_item.findtext('description') or '').strip()
            link = (rss_item.findtext('link') or url).strip()
            pub_date = parse_rss_date(rss_item.findtext('pubDate') or '')
            guid = (rss_item.findtext('guid') or title).strip()

            # Nettoyer description HTML si présent
            import re
            description = re.sub(r'<[^>]+>', ' ', description).strip()
            description = re.sub(r'\s+', ' ', description)[:400]

            if not title:
                continue

            item = CTQItem(
                section=feed_config["section"],
                section_label=feed_config["label"],
                icon=feed_config["icon"],
                priority=feed_config["priority"],
                title=title,
                description=description,
                url=link if link.startswith('http') else url,
                date_publie=pub_date,
                hash_id=make_hash(guid + title),
                tags=detect_tags(title + " " + description),
                source="rss",
            )
            items.append(item)

    except ET.ParseError as e:
        log.error(f"RSS {feed_key} — Erreur XML: {e}")
    except Exception as e:
        log.error(f"RSS {feed_key} — Erreur: {e}")

    return items


# ─── HTML SCRAPER (fallback + sections additionnelles) ───────────────────────

def fetch_html_section(section_key: str, section_config: dict) -> list[CTQItem]:
    """Scrape une section HTML du site CTQ."""
    items = []
    today_str = date.today().isoformat()

    try:
        from bs4 import BeautifulSoup
        resp = requests.get(
            section_config["url"],
            headers={**HEADERS, "Accept": "text/html"},
            timeout=20,
            verify=True,
        )
        if resp.status_code != 200:
            return items

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Chercher liens d'actualités
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if any(pattern in href for pattern in ['/actualites/detail/', '/decisions/', 'QCCTQ']) and len(text) > 15:
                full_url = "https://www.ctq.gouv.qc.ca" + href if href.startswith('/') else href
                item = CTQItem(
                    section=section_key,
                    section_label=section_config["label"],
                    icon=section_config["icon"],
                    priority=section_config["priority"],
                    title=text[:150],
                    description="",
                    url=full_url,
                    date_publie=today_str,
                    hash_id=make_hash(href + text),
                    tags=detect_tags(text),
                    source="html",
                )
                items.append(item)

    except Exception as e:
        log.error(f"HTML {section_key}: {e}")

    return items[:15]


# ─── DIFF ENGINE ─────────────────────────────────────────────────────────────

def load_known_hashes() -> set:
    path = os.path.join(DATA_DIR, "known_hashes.json")
    if os.path.exists(path):
        with open(path) as f:
            return set(json.load(f))
    return set()


def save_known_hashes(hashes: set):
    path = os.path.join(DATA_DIR, "known_hashes.json")
    with open(path, "w") as f:
        json.dump(list(hashes), f)


def save_daily_report(items: list[CTQItem], new_items: list[CTQItem]) -> dict:
    today = date.today().isoformat()

    # Compter par section originale
    def count_section(section_items, key):
        return len([i for i in section_items if i.section == key])

    report = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "total_items": len(items),
        "new_items_count": len(new_items),
        "new_items": [asdict(i) for i in new_items],
        "all_items": [asdict(i) for i in items],
        "summary": {
            "avis_publics": count_section(new_items, "avis_publics"),
            "calendrier_audiences": count_section(new_items, "calendrier_audiences"),
            "decisions": count_section(new_items, "decisions"),
            "actualites": count_section(new_items, "actualites"),
        },
        "rss_feeds": list(RSS_FEEDS.keys()),
    }

    for path in [
        os.path.join(DATA_DIR, f"report_{today}.json"),
        os.path.join(DATA_DIR, "latest_report.json"),
    ]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    log.info(f"Rapport sauvegardé — {len(new_items)} nouveaux items")
    return report


# ─── ORCHESTRATEUR ───────────────────────────────────────────────────────────

def run_scraper() -> dict:
    log.info("=== CTQ Veille v2.0 — RSS + HTML ===")
    known = load_known_hashes()
    all_items = []

    # 1. Flux RSS officiels (source primaire)
    log.info("── Flux RSS CTQ ──")
    for feed_key, feed_config in RSS_FEEDS.items():
        try:
            items = fetch_rss_feed(feed_key, feed_config)
            all_items.extend(items)
            time.sleep(1)
        except Exception as e:
            log.error(f"Erreur RSS {feed_key}: {e}")

    # 2. Sections HTML additionnelles
    log.info("── Sections HTML CTQ ──")
    for section_key, section_config in HTML_SECTIONS.items():
        try:
            items = fetch_html_section(section_key, section_config)
            all_items.extend(items)
            time.sleep(1.5)
        except Exception as e:
            log.error(f"Erreur HTML {section_key}: {e}")

    # Dédoublonner
    seen = set()
    unique_items = []
    for item in all_items:
        if item.hash_id not in seen:
            seen.add(item.hash_id)
            unique_items.append(item)
    all_items = unique_items

    # Détecter nouveautés
    new_hashes = set()
    new_items = []
    for item in all_items:
        new_hashes.add(item.hash_id)
        if item.hash_id not in known:
            item.is_new = True
            new_items.append(item)

    log.info(f"Total: {len(all_items)} items | Nouveaux: {len(new_items)}")

    save_known_hashes(known | new_hashes)
    return save_daily_report(all_items, new_items)


if __name__ == "__main__":
    report = run_scraper()
    print(f"\n✅ Scraping terminé — {report['new_items_count']} nouveaux éléments")
