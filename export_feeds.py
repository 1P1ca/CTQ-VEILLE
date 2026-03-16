"""
Exporte les données RSS parsées en JSON statique pour le dashboard.
Appelé par run_daily.py après le scraping.
"""
import json, os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

def export_feeds_json(report):
    """Écrit docs/feeds.json avec toutes les données RSS parsées."""
    feeds_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        "items": report.get("all_items", []),
        "new_count": report.get("new_items_count", 0),
        "summary": report.get("summary", {}),
    }
    
    output = os.path.join(DOCS_DIR, "feeds.json")
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(feeds_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ feeds.json exporté: {len(feeds_data['items'])} items")
    return output
