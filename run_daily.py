"""
CTQ Veille - Orchestrateur principal
Exécuté chaque matin par GitHub Actions
"""

import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ctq_main")


def main():
    log.info("=" * 60)
    log.info("CTQ VEILLE — Démarrage du cycle quotidien")
    log.info("=" * 60)

    # 1. SCRAPER
    log.info("Étape 1/3 — Scraping CTQ...")
    try:
        from scraper import run_scraper
        report = run_scraper()
        log.info(f"✅ Scraping OK — {report['new_items_count']} nouveaux éléments")
    except Exception as e:
        log.error(f"❌ Scraping ÉCHOUÉ: {e}")
        sys.exit(1)

    # 2. DASHBOARD
    log.info("Étape 2/3 — Génération du dashboard...")
    try:
        from generate_dashboard import generate_dashboard
        generate_dashboard()
        log.info("✅ Dashboard généré")
    except Exception as e:
        log.error(f"❌ Dashboard ÉCHOUÉ: {e}")

    # 3. COURRIEL
    log.info("Étape 3/3 — Envoi du rapport courriel...")
    try:
        from email_report import send_email
        success = send_email(report)
        if success:
            log.info("✅ Courriel envoyé")
        else:
            log.warning("⚠️  Courriel non envoyé (SMTP non configuré ou erreur)")
    except Exception as e:
        log.error(f"❌ Courriel ÉCHOUÉ: {e}")

    log.info("=" * 60)
    log.info(f"CTQ VEILLE — Cycle terminé | Nouveaux: {report['new_items_count']}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
