"""
CTQ Veille - Scraper
Surveille les 4 sections dynamiques de ctq.gouv.qc.ca
"""

import requests
from bs4 import BeautifulSoup
import json
import hashlib
import os
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import Optional
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ctq_scraper")

BASE_URL = "https://www.ctq.gouv.qc.ca"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CTQ-Veille/1.0; +contact@1p1.ca)",
    "Accept-Language": "fr-CA,fr;q=0.9",
}

SECTIONS = {
    "avis_publics": {
        "label": "Avis publics",
        "url": f"{BASE_URL}/services-en-ligne/",
        "icon": "📋",
        "priority": "haute",
    },
    "calendrier_audiences": {
        "label": "Calendrier des audiences",
        "url": f"{BASE_URL}/la-commission/laudience/",
        "icon": "🗓️",
        "priority": "haute",
    },
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

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


def fetch_page(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        log.error(f"Erreur fetch {url}: {e}")
        return None


def make_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def detect_tags(text: str) -> list:
    """Détecte les tags pertinents pour le secteur autobus/coach."""
    text_lower = text.lower()
    tags = []
    keyword_map = {
        "Nouveau permis": ["nouveau permis", "demande de permis"],
        "Transfert": ["transfert", "cession"],
        "Modification territoire": ["territoire", "municipalité", "agglomération"],
        "Nolisé": ["nolisé", "nolise", "charte"],
        "Transport scolaire": ["scolaire", "élèves", "écoliers"],
        "Révocation": ["révocation", "révoqué", "suspension"],
        "Interurbain": ["interurbain"],
        "Urbain": ["urbain"],
        "Audience": ["audience"],
        "Tarification": ["tarif", "indexation", "prix"],
        "VFÉ": ["faibles émissions", "électrique", "vfe"],
    }
    for tag, keywords in keyword_map.items():
        if any(k in text_lower for k in keywords):
            tags.append(tag)
    return tags


# ─── SECTION SCRAPERS ───────────────────────────────────────────────────────


def scrape_avis_publics() -> list[CTQItem]:
    """Scrape la page des avis publics autobus."""
    items = []
    soup = fetch_page(SECTIONS["avis_publics"]["url"])
    if not soup:
        return items

    # La CTQ publie les avis en tableau ou liste — on cherche les entrées texte
    today_str = date.today().isoformat()

    # Chercher tables ou listes d'avis
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:  # Skip header
            cols = row.find_all(["td", "th"])
            if len(cols) >= 2:
                title = cols[0].get_text(strip=True)
                desc = " | ".join(c.get_text(strip=True) for c in cols[1:])
                link = cols[0].find("a")
                url = BASE_URL + link["href"] if link and link.get("href", "").startswith("/") else (link["href"] if link else SECTIONS["avis_publics"]["url"])
                if title:
                    item = CTQItem(
                        section="avis_publics",
                        section_label=SECTIONS["avis_publics"]["label"],
                        icon=SECTIONS["avis_publics"]["icon"],
                        priority=SECTIONS["avis_publics"]["priority"],
                        title=title,
                        description=desc[:300],
                        url=url,
                        date_publie=today_str,
                        hash_id=make_hash(title + desc),
                        tags=detect_tags(title + " " + desc),
                    )
                    items.append(item)

    # Fallback: paragraphes / divs contenant avis
    if not items:
        for elem in soup.find_all(["p", "li", "div"], class_=lambda c: c and ("avis" in c.lower() or "notice" in c.lower())):
            text = elem.get_text(strip=True)
            if len(text) > 30:
                link = elem.find("a")
                url = BASE_URL + link["href"] if link and link.get("href", "").startswith("/") else SECTIONS["avis_publics"]["url"]
                item = CTQItem(
                    section="avis_publics",
                    section_label=SECTIONS["avis_publics"]["label"],
                    icon=SECTIONS["avis_publics"]["icon"],
                    priority=SECTIONS["avis_publics"]["priority"],
                    title=text[:100],
                    description=text[:300],
                    url=url,
                    date_publie=today_str,
                    hash_id=make_hash(text),
                    tags=detect_tags(text),
                )
                items.append(item)

    log.info(f"Avis publics: {len(items)} entrées trouvées")
    return items


def scrape_calendrier() -> list[CTQItem]:
    """Scrape le calendrier des audiences."""
    items = []
    soup = fetch_page(SECTIONS["calendrier_audiences"]["url"])
    if not soup:
        return items

    today_str = date.today().isoformat()

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            if len(cols) >= 2:
                date_audience = cols[0].get_text(strip=True)
                title = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                desc = " | ".join(c.get_text(strip=True) for c in cols[2:]) if len(cols) > 2 else ""
                link = row.find("a")
                url = BASE_URL + link["href"] if link and link.get("href", "").startswith("/") else SECTIONS["calendrier_audiences"]["url"]
                if title:
                    item = CTQItem(
                        section="calendrier_audiences",
                        section_label=SECTIONS["calendrier_audiences"]["label"],
                        icon=SECTIONS["calendrier_audiences"]["icon"],
                        priority=SECTIONS["calendrier_audiences"]["priority"],
                        title=f"{date_audience} — {title}" if date_audience else title,
                        description=desc[:300],
                        url=url,
                        date_publie=today_str,
                        hash_id=make_hash(date_audience + title),
                        tags=detect_tags(title + " " + desc),
                    )
                    items.append(item)

    # Fallback paragraphes
    if not items:
        for p in soup.find_all(["p", "li"]):
            text = p.get_text(strip=True)
            if len(text) > 40 and any(kw in text.lower() for kw in ["audience", "séance", "autobus", "transport"]):
                item = CTQItem(
                    section="calendrier_audiences",
                    section_label=SECTIONS["calendrier_audiences"]["label"],
                    icon=SECTIONS["calendrier_audiences"]["icon"],
                    priority=SECTIONS["calendrier_audiences"]["priority"],
                    title=text[:100],
                    description=text[:300],
                    url=SECTIONS["calendrier_audiences"]["url"],
                    date_publie=today_str,
                    hash_id=make_hash(text),
                    tags=detect_tags(text),
                )
                items.append(item)

    log.info(f"Calendrier audiences: {len(items)} entrées trouvées")
    return items


def scrape_decisions() -> list[CTQItem]:
    """Scrape les décisions récentes - autobus prioritairement."""
    items = []
    # La recherche de décisions est un formulaire en ligne — on scrape la page principale
    # et on peut aussi requêter avec des filtres
    soup = fetch_page(SECTIONS["decisions"]["url"])
    if not soup:
        return items

    today_str = date.today().isoformat()

    # Chercher liens vers décisions récentes
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        # Filtrer les décisions autobus (contiennent "QCCTQ" dans l'URL ou le texte)
        if ("decision" in href.lower() or "QCCTQ" in text or "autobus" in text.lower()) and len(text) > 10:
            full_url = BASE_URL + href if href.startswith("/") else href
            item = CTQItem(
                section="decisions",
                section_label=SECTIONS["decisions"]["label"],
                icon=SECTIONS["decisions"]["icon"],
                priority=SECTIONS["decisions"]["priority"],
                title=text[:150],
                description=f"Décision disponible: {text[:200]}",
                url=full_url,
                date_publie=today_str,
                hash_id=make_hash(href + text),
                tags=detect_tags(text),
            )
            items.append(item)

    log.info(f"Décisions: {len(items)} entrées trouvées")
    return items[:20]  # Limiter à 20


def scrape_actualites() -> list[CTQItem]:
    """Scrape les actualités et dossiers prioritaires."""
    items = []
    soup = fetch_page(SECTIONS["actualites"]["url"])
    if not soup:
        return items

    today_str = date.today().isoformat()

    # Chercher articles/actualités
    for article in soup.find_all(["article", "div"], class_=lambda c: c and any(k in str(c).lower() for k in ["actu", "news", "item", "post"])):
        title_elem = article.find(["h2", "h3", "h4", "strong"])
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        desc_elem = article.find("p")
        desc = desc_elem.get_text(strip=True) if desc_elem else ""
        link = article.find("a")
        url = BASE_URL + link["href"] if link and link.get("href", "").startswith("/") else SECTIONS["actualites"]["url"]

        # Date
        date_elem = article.find(["time", "span"], class_=lambda c: c and "date" in str(c).lower())
        pub_date = date_elem.get_text(strip=True) if date_elem else today_str

        if title and len(title) > 10:
            item = CTQItem(
                section="actualites",
                section_label=SECTIONS["actualites"]["label"],
                icon=SECTIONS["actualites"]["icon"],
                priority=SECTIONS["actualites"]["priority"],
                title=title,
                description=desc[:300],
                url=url,
                date_publie=pub_date,
                hash_id=make_hash(title),
                tags=detect_tags(title + " " + desc),
            )
            items.append(item)

    # Fallback: chercher tous les liens d'actualités
    if not items:
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if "/actualites/detail/" in href and len(text) > 15:
                full_url = BASE_URL + href if href.startswith("/") else href
                item = CTQItem(
                    section="actualites",
                    section_label=SECTIONS["actualites"]["label"],
                    icon=SECTIONS["actualites"]["icon"],
                    priority=SECTIONS["actualites"]["priority"],
                    title=text,
                    description="",
                    url=full_url,
                    date_publie=today_str,
                    hash_id=make_hash(href),
                    tags=detect_tags(text),
                )
                items.append(item)

    log.info(f"Actualités: {len(items)} entrées trouvées")
    return items


# ─── DIFF ENGINE ────────────────────────────────────────────────────────────


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


def save_daily_report(items: list[CTQItem], new_items: list[CTQItem]):
    today = date.today().isoformat()
    report = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "total_items": len(items),
        "new_items_count": len(new_items),
        "new_items": [asdict(i) for i in new_items],
        "all_items": [asdict(i) for i in items],
        "summary": {
            "avis_publics": len([i for i in new_items if i.section == "avis_publics"]),
            "calendrier_audiences": len([i for i in new_items if i.section == "calendrier_audiences"]),
            "decisions": len([i for i in new_items if i.section == "decisions"]),
            "actualites": len([i for i in new_items if i.section == "actualites"]),
        },
    }
    path = os.path.join(DATA_DIR, f"report_{today}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # Also save as latest
    latest_path = os.path.join(DATA_DIR, "latest_report.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    log.info(f"Rapport sauvegardé: {path}")
    return report


def run_scraper() -> dict:
    log.info("=== CTQ Veille — Démarrage du scraping ===")
    known = load_known_hashes()
    all_items = []

    scrapers = [
        scrape_avis_publics,
        scrape_calendrier,
        scrape_decisions,
        scrape_actualites,
    ]

    for scraper_fn in scrapers:
        try:
            items = scraper_fn()
            all_items.extend(items)
            time.sleep(2)  # Respecter le serveur
        except Exception as e:
            log.error(f"Erreur scraper {scraper_fn.__name__}: {e}")

    # Identifier les nouveautés
    new_hashes = set()
    new_items = []
    for item in all_items:
        new_hashes.add(item.hash_id)
        if item.hash_id not in known:
            item.is_new = True
            new_items.append(item)

    log.info(f"Total: {len(all_items)} items | Nouveaux: {len(new_items)}")

    # Mettre à jour les hashes connus
    save_known_hashes(known | new_hashes)

    # Sauvegarder le rapport
    report = save_daily_report(all_items, new_items)
    return report


if __name__ == "__main__":
    report = run_scraper()
    print(f"\n✅ Scraping terminé — {report['new_items_count']} nouveaux éléments détectés")
