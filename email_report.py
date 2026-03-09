"""
CTQ Veille - Générateur et envoi du rapport courriel quotidien
Utilise Gmail SMTP (ou tout autre SMTP) via variables d'environnement GitHub Secrets
"""

import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, datetime
import logging

log = logging.getLogger("ctq_email")

# ─── CONFIG (via GitHub Secrets) ────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "nancy@groupemenard.com")
SENDER_NAME = os.getenv("SENDER_NAME", "CTQ Veille — 1+1 Discovery")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://YOUR_ORG.github.io/ctq-veille/")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

PRIORITY_COLOR = {
    "haute": "#E84B1C",
    "moyenne": "#F5A623",
    "basse": "#7ED321",
}

TAG_COLOR = {
    "Nouveau permis": "#E84B1C",
    "Transfert": "#9B59B6",
    "Modification territoire": "#3498DB",
    "Nolisé": "#1ABC9C",
    "Transport scolaire": "#F39C12",
    "Révocation": "#E74C3C",
    "Interurbain": "#2980B9",
    "Urbain": "#27AE60",
    "Audience": "#8E44AD",
    "Tarification": "#E67E22",
    "VFÉ": "#2ECC71",
}


def load_latest_report() -> dict:
    path = os.path.join(DATA_DIR, "latest_report.json")
    if not os.path.exists(path):
        raise FileNotFoundError("Aucun rapport trouvé. Lancer scraper.py d'abord.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render_tag(tag: str) -> str:
    color = TAG_COLOR.get(tag, "#666")
    return f'<span style="display:inline-block;background:{color};color:white;font-size:10px;font-weight:700;padding:2px 7px;border-radius:3px;margin:1px 2px;letter-spacing:0.5px;">{tag}</span>'


def render_item_card(item: dict) -> str:
    tags_html = "".join(render_tag(t) for t in item.get("tags", []))
    priority = item.get("priority", "moyenne")
    border_color = PRIORITY_COLOR.get(priority, "#ccc")
    new_badge = '<span style="background:#E84B1C;color:white;font-size:10px;font-weight:800;padding:2px 8px;border-radius:2px;margin-left:8px;letter-spacing:1px;">NOUVEAU</span>' if item.get("is_new") else ""

    return f"""
    <div style="border-left:4px solid {border_color};background:#fff;padding:14px 16px;margin-bottom:10px;border-radius:0 6px 6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:4px;">
            {item.get('icon','')} {item.get('title','')} {new_badge}
        </div>
        {f'<div style="font-size:12px;color:#555;margin-bottom:6px;">{item["description"][:200]}</div>' if item.get("description") else ""}
        <div style="margin-bottom:6px;">{tags_html}</div>
        <div style="font-size:11px;color:#999;">
            📅 {item.get('date_publie','')} &nbsp;|&nbsp;
            <a href="{item.get('url','#')}" style="color:#E84B1C;text-decoration:none;font-weight:600;">Voir sur CTQ →</a>
        </div>
    </div>
    """


def render_section_block(section_key: str, section_label: str, icon: str, items: list) -> str:
    if not items:
        return f"""
        <div style="margin-bottom:24px;">
            <div style="font-size:15px;font-weight:800;color:#1a1a2e;border-bottom:2px solid #f0f0f0;padding-bottom:6px;margin-bottom:10px;">{icon} {section_label}</div>
            <div style="color:#aaa;font-size:12px;font-style:italic;">Aucune nouvelle activité détectée aujourd'hui.</div>
        </div>
        """
    cards = "".join(render_item_card(i) for i in items)
    new_count = sum(1 for i in items if i.get("is_new"))
    badge = f'<span style="background:#E84B1C;color:white;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px;">{new_count} nouveau{"x" if new_count > 1 else ""}</span>' if new_count > 0 else ""
    return f"""
    <div style="margin-bottom:28px;">
        <div style="font-size:15px;font-weight:800;color:#1a1a2e;border-bottom:2px solid #E84B1C;padding-bottom:8px;margin-bottom:12px;">
            {icon} {section_label} {badge}
        </div>
        {cards}
    </div>
    """


def build_html_email(report: dict) -> str:
    today = report.get("date", date.today().isoformat())
    new_count = report.get("new_items_count", 0)
    all_items = report.get("all_items", [])
    new_items = report.get("new_items", [])
    summary = report.get("summary", {})
    generated_at = report.get("generated_at", datetime.now().isoformat())[:16].replace("T", " à ")

    # Grouper par section
    sections_config = [
        ("avis_publics", "Avis publics", "📋"),
        ("calendrier_audiences", "Calendrier des audiences", "🗓️"),
        ("decisions", "Décisions rendues", "⚖️"),
        ("actualites", "Actualités & dossiers prioritaires", "📢"),
    ]

    sections_html = ""
    for key, label, icon in sections_config:
        section_items = [i for i in all_items if i.get("section") == key]
        sections_html += render_section_block(key, label, icon, section_items)

    # Résumé stat
    total_new = sum(summary.values())
    stat_items = "".join([
        f'<td style="text-align:center;padding:8px 16px;"><div style="font-size:24px;font-weight:800;color:#E84B1C;">{summary.get(k, 0)}</div><div style="font-size:10px;color:#888;margin-top:2px;">{lbl}</div></td>'
        for k, lbl in [
            ("avis_publics", "Avis publics"),
            ("calendrier_audiences", "Audiences"),
            ("decisions", "Décisions"),
            ("actualites", "Actualités"),
        ]
    ])

    alert_bar = ""
    if total_new > 0:
        alert_bar = f'<div style="background:#E84B1C;color:white;padding:12px 20px;text-align:center;font-size:13px;font-weight:700;letter-spacing:0.5px;">🚨 {total_new} nouveau{"x" if total_new > 1 else ""} élément{"s" if total_new > 1 else ""} détecté{"s" if total_new > 1 else ""} aujourd\'hui</div>'
    else:
        alert_bar = '<div style="background:#27AE60;color:white;padding:12px 20px;text-align:center;font-size:13px;font-weight:600;">✅ Aucun nouveau mouvement — situation stable</div>'

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:'Segoe UI',Arial,sans-serif;">

<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

  <!-- HEADER -->
  <div style="background:#1a1a2e;padding:24px 28px 20px;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:11px;color:#E84B1C;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Rapport Quotidien</div>
        <div style="font-size:22px;font-weight:800;color:#ffffff;">CTQ Veille</div>
        <div style="font-size:12px;color:#8892a4;margin-top:2px;">Commission des transports du Québec</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:20px;font-weight:800;color:#E84B1C;">{today}</div>
        <div style="font-size:11px;color:#666;margin-top:2px;">Généré à {generated_at[11:]}</div>
      </div>
    </div>
  </div>

  {alert_bar}

  <!-- STATS -->
  <div style="background:#f9f9fb;padding:16px 20px;border-bottom:1px solid #eee;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>{stat_items}</tr>
    </table>
  </div>

  <!-- CONTENT -->
  <div style="padding:24px 28px;">
    {sections_html}
  </div>

  <!-- FOOTER -->
  <div style="background:#1a1a2e;padding:16px 28px;text-align:center;">
    <div style="font-size:11px;color:#555;margin-bottom:8px;">
      <a href="{DASHBOARD_URL}" style="color:#E84B1C;font-weight:700;text-decoration:none;">📊 Voir le dashboard complet</a>
      &nbsp;&nbsp;|&nbsp;&nbsp;
      <a href="https://www.ctq.gouv.qc.ca" style="color:#8892a4;text-decoration:none;">ctq.gouv.qc.ca</a>
    </div>
    <div style="font-size:10px;color:#444;">Ce rapport est généré automatiquement par 1+1 Discovery · Pour Nancy M. · Ne pas répondre à ce courriel</div>
  </div>

</div>
</body>
</html>"""


def build_text_email(report: dict) -> str:
    today = report.get("date", date.today().isoformat())
    new_items = report.get("new_items", [])
    summary = report.get("summary", {})

    lines = [
        f"CTQ VEILLE — {today}",
        "=" * 50,
        f"Nouveaux éléments: {report.get('new_items_count', 0)}",
        f"  • Avis publics: {summary.get('avis_publics', 0)}",
        f"  • Audiences: {summary.get('calendrier_audiences', 0)}",
        f"  • Décisions: {summary.get('decisions', 0)}",
        f"  • Actualités: {summary.get('actualites', 0)}",
        "",
    ]

    for item in new_items:
        lines.append(f"[{item.get('section_label', '')}] {item.get('title', '')}")
        if item.get("description"):
            lines.append(f"  {item['description'][:150]}")
        lines.append(f"  → {item.get('url', '')}")
        lines.append("")

    lines.append(f"Dashboard: {DASHBOARD_URL}")
    lines.append("Rapport généré par 1+1 Discovery")
    return "\n".join(lines)


def send_email(report: dict):
    if not SMTP_USER or not SMTP_PASSWORD:
        log.warning("SMTP non configuré — rapport non envoyé (mode local)")
        print("⚠️  Variables SMTP manquantes. Configurer dans GitHub Secrets.")
        return False

    today = report.get("date", date.today().isoformat())
    new_count = report.get("new_items_count", 0)

    subject_prefix = "🚨" if new_count > 0 else "✅"
    subject = f"{subject_prefix} CTQ Veille {today} — {new_count} nouveau{'x' if new_count > 1 else ''}" if new_count > 0 else f"✅ CTQ Veille {today} — Aucun mouvement"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECIPIENT_EMAIL

    msg.attach(MIMEText(build_text_email(report), "plain", "utf-8"))
    msg.attach(MIMEText(build_html_email(report), "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, RECIPIENT_EMAIL, msg.as_string())
        log.info(f"✅ Rapport envoyé à {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        log.error(f"Erreur envoi courriel: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    report = load_latest_report()
    html = build_html_email(report)
    # Sauvegarder preview HTML
    preview_path = os.path.join(DATA_DIR, "email_preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Preview HTML: {preview_path}")
    send_email(report)
