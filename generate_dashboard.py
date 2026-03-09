"""
CTQ Veille - Générateur du dashboard HTML statique
Produit docs/index.html pour GitHub Pages
"""

import json
import os
from datetime import date, datetime
from pathlib import Path

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
os.makedirs(DOCS_DIR, exist_ok=True)


def load_latest_report() -> dict:
    path = os.path.join(DATA_DIR, "latest_report.json")
    if not os.path.exists(path):
        return {
            "date": date.today().isoformat(),
            "generated_at": datetime.now().isoformat(),
            "total_items": 0,
            "new_items_count": 0,
            "new_items": [],
            "all_items": [],
            "summary": {"avis_publics": 0, "calendrier_audiences": 0, "decisions": 0, "actualites": 0},
        }
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_history() -> list:
    """Charge les 30 derniers rapports pour le graphique historique."""
    reports = []
    data_path = Path(DATA_DIR)
    report_files = sorted(data_path.glob("report_*.json"), reverse=True)[:30]
    for f in report_files:
        with open(f, encoding="utf-8") as fp:
            r = json.load(fp)
            reports.append({
                "date": r.get("date"),
                "new_count": r.get("new_items_count", 0),
                "total": r.get("total_items", 0),
            })
    return list(reversed(reports))


def build_dashboard(report: dict, history: list) -> str:
    today = report.get("date", date.today().isoformat())
    new_count = report.get("new_items_count", 0)
    all_items = report.get("all_items", [])
    summary = report.get("summary", {})
    generated_at = report.get("generated_at", "")[:16].replace("T", " à ")

    items_json = json.dumps(all_items, ensure_ascii=False)
    history_json = json.dumps(history, ensure_ascii=False)
    summary_json = json.dumps(summary, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CTQ Veille — Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --red: #E84B1C;
    --dark: #0f0f1a;
    --dark2: #1a1a2e;
    --dark3: #16213e;
    --card: #1e1e32;
    --border: rgba(255,255,255,0.07);
    --text: #e8e8f0;
    --muted: #8892a4;
    --avis: #E84B1C;
    --audience: #3B82F6;
    --decision: #8B5CF6;
    --actu: #10B981;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--dark);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ── TOP BAR ── */
  .topbar {{
    background: var(--dark2);
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .topbar-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .logo-dot {{
    width: 10px; height: 10px;
    background: var(--red);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0%,100% {{ opacity:1; transform:scale(1); }}
    50% {{ opacity:0.5; transform:scale(1.4); }}
  }}
  .brand-text {{ font-family:'Syne',sans-serif; font-weight:800; font-size:16px; letter-spacing:0.5px; }}
  .brand-sub {{ font-size:11px; color:var(--muted); margin-left:4px; }}
  .topbar-meta {{ font-size:11px; color:var(--muted); text-align:right; }}
  .topbar-meta strong {{ color:var(--red); }}

  /* ── LAYOUT ── */
  .main {{ max-width:1280px; margin:0 auto; padding:28px 24px; }}

  /* ── ALERT BANNER ── */
  .alert-banner {{
    border-radius:8px;
    padding:14px 20px;
    margin-bottom:24px;
    font-weight:600;
    font-size:14px;
    display:flex;
    align-items:center;
    gap:10px;
  }}
  .alert-new {{ background:rgba(232,75,28,0.15); border:1px solid rgba(232,75,28,0.4); color:#ff7f5c; }}
  .alert-ok {{ background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); color:#34d399; }}

  /* ── STATS ── */
  .stats-grid {{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:14px;
    margin-bottom:24px;
  }}
  .stat-card {{
    background:var(--card);
    border:1px solid var(--border);
    border-radius:10px;
    padding:18px 20px;
    position:relative;
    overflow:hidden;
  }}
  .stat-card::before {{
    content:'';
    position:absolute;
    top:0; left:0; right:0;
    height:3px;
  }}
  .stat-card.avis::before {{ background:var(--avis); }}
  .stat-card.audience::before {{ background:var(--audience); }}
  .stat-card.decision::before {{ background:var(--decision); }}
  .stat-card.actu::before {{ background:var(--actu); }}
  .stat-number {{ font-family:'Syne',sans-serif; font-size:32px; font-weight:800; line-height:1; }}
  .stat-label {{ font-size:11px; color:var(--muted); margin-top:4px; text-transform:uppercase; letter-spacing:0.8px; }}
  .stat-icon {{ position:absolute; right:16px; top:16px; font-size:22px; opacity:0.3; }}

  /* ── GRID LAYOUT ── */
  .content-grid {{
    display:grid;
    grid-template-columns:1fr 340px;
    gap:20px;
  }}

  /* ── SECTION PANEL ── */
  .panel {{
    background:var(--card);
    border:1px solid var(--border);
    border-radius:10px;
    overflow:hidden;
    margin-bottom:16px;
  }}
  .panel-header {{
    padding:14px 18px;
    border-bottom:1px solid var(--border);
    display:flex;
    align-items:center;
    justify-content:space-between;
  }}
  .panel-title {{
    font-family:'Syne',sans-serif;
    font-weight:700;
    font-size:13px;
    letter-spacing:0.5px;
    text-transform:uppercase;
    display:flex;
    align-items:center;
    gap:8px;
  }}
  .new-badge {{
    background:var(--red);
    color:white;
    font-size:10px;
    font-weight:700;
    padding:2px 7px;
    border-radius:3px;
    letter-spacing:0.5px;
  }}
  .panel-body {{ padding:14px 18px; }}

  /* ── ITEM CARD ── */
  .item-card {{
    border-left:3px solid;
    padding:10px 14px;
    margin-bottom:8px;
    border-radius:0 6px 6px 0;
    background:rgba(255,255,255,0.03);
    transition:background 0.2s;
    cursor:pointer;
  }}
  .item-card:hover {{ background:rgba(255,255,255,0.07); }}
  .item-card.new-item {{ background:rgba(232,75,28,0.08); }}
  .item-card.section-avis {{ border-color:var(--avis); }}
  .item-card.section-audience {{ border-color:var(--audience); }}
  .item-card.section-decision {{ border-color:var(--decision); }}
  .item-card.section-actu {{ border-color:var(--actu); }}
  .item-title {{ font-size:13px; font-weight:600; color:var(--text); margin-bottom:4px; }}
  .item-desc {{ font-size:11px; color:var(--muted); margin-bottom:6px; line-height:1.4; }}
  .item-footer {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
  .item-date {{ font-size:10px; color:var(--muted); }}
  .item-link {{ font-size:10px; color:var(--red); text-decoration:none; font-weight:600; }}
  .item-link:hover {{ text-decoration:underline; }}
  .tag {{
    display:inline-block;
    font-size:9px;
    font-weight:700;
    padding:1px 6px;
    border-radius:2px;
    letter-spacing:0.5px;
    text-transform:uppercase;
    color:white;
  }}
  .empty-state {{ text-align:center; padding:20px; color:var(--muted); font-size:12px; }}

  /* ── SIDEBAR ── */
  .sidebar-panel {{
    background:var(--card);
    border:1px solid var(--border);
    border-radius:10px;
    margin-bottom:16px;
    overflow:hidden;
  }}
  .sidebar-header {{
    padding:12px 16px;
    border-bottom:1px solid var(--border);
    font-family:'Syne',sans-serif;
    font-size:12px;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:0.8px;
    color:var(--muted);
  }}
  .sidebar-body {{ padding:14px 16px; }}

  /* ── FILTER BAR ── */
  .filter-bar {{
    display:flex;
    gap:8px;
    margin-bottom:16px;
    flex-wrap:wrap;
  }}
  .filter-btn {{
    background:var(--card);
    border:1px solid var(--border);
    color:var(--muted);
    padding:6px 14px;
    border-radius:20px;
    font-size:11px;
    font-weight:600;
    cursor:pointer;
    transition:all 0.2s;
    font-family:'DM Sans',sans-serif;
  }}
  .filter-btn.active, .filter-btn:hover {{
    border-color:var(--red);
    color:var(--red);
    background:rgba(232,75,28,0.1);
  }}

  /* ── HISTORY CHART ── */
  .chart-container {{ height:100px; position:relative; }}
  .chart-bars {{ display:flex; align-items:flex-end; gap:3px; height:80px; }}
  .bar {{ flex:1; border-radius:2px 2px 0 0; min-width:6px; transition:opacity 0.2s; cursor:pointer; position:relative; }}
  .bar:hover {{ opacity:0.8; }}
  .chart-labels {{ display:flex; justify-content:space-between; margin-top:4px; }}
  .chart-label {{ font-size:9px; color:var(--muted); }}

  /* ── SEARCH ── */
  .search-input {{
    width:100%;
    background:var(--dark3);
    border:1px solid var(--border);
    border-radius:6px;
    color:var(--text);
    padding:8px 12px;
    font-size:12px;
    font-family:'DM Sans',sans-serif;
    outline:none;
    margin-bottom:12px;
  }}
  .search-input:focus {{ border-color:var(--red); }}

  /* ── RESPONSIVE ── */
  @media(max-width:900px) {{
    .stats-grid {{ grid-template-columns:repeat(2,1fr); }}
    .content-grid {{ grid-template-columns:1fr; }}
  }}

  /* ── SCROLL ── */
  ::-webkit-scrollbar {{ width:4px; }}
  ::-webkit-scrollbar-track {{ background:var(--dark); }}
  ::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-brand">
    <div class="logo-dot"></div>
    <div>
      <span class="brand-text">CTQ Veille</span>
      <span class="brand-sub">Commission des transports du Québec</span>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <a href="analytics.html" style="display:flex;align-items:center;gap:6px;background:rgba(232,75,28,0.12);border:1px solid rgba(232,75,28,0.3);color:#ff7f5c;text-decoration:none;font-size:12px;font-weight:600;padding:6px 14px;border-radius:6px;transition:background 0.2s;" onmouseover="this.style.background='rgba(232,75,28,0.22)'" onmouseout="this.style.background='rgba(232,75,28,0.12)'">📊 Analytique des permis</a>
    <div class="topbar-meta">
      Rapport du <strong>{today}</strong><br>
      Généré à {generated_at[11:] if 'à' in generated_at else generated_at}
    </div>
  </div>
</div>

<div class="main">

  <!-- ALERT -->
  <div id="alertBanner" class="alert-banner {'alert-new' if new_count > 0 else 'alert-ok'}">
    {'🚨' if new_count > 0 else '✅'}
    {'<strong>' + str(new_count) + ' nouveau' + ('x' if new_count > 1 else '') + ' élément' + ('s' if new_count > 1 else '') + '</strong> détecté' + ('s' if new_count > 1 else '') + ' aujourd\'hui sur le site de la CTQ' if new_count > 0 else 'Aucun nouveau mouvement détecté — situation stable'}
  </div>

  <!-- STATS -->
  <div class="stats-grid">
    <div class="stat-card avis">
      <div class="stat-icon">📋</div>
      <div class="stat-number" id="statAvis">{summary.get("avis_publics", 0)}</div>
      <div class="stat-label">Avis publics</div>
    </div>
    <div class="stat-card audience">
      <div class="stat-icon">🗓️</div>
      <div class="stat-number" id="statAudience">{summary.get("calendrier_audiences", 0)}</div>
      <div class="stat-label">Audiences</div>
    </div>
    <div class="stat-card decision">
      <div class="stat-icon">⚖️</div>
      <div class="stat-number" id="statDecision">{summary.get("decisions", 0)}</div>
      <div class="stat-label">Décisions</div>
    </div>
    <div class="stat-card actu">
      <div class="stat-icon">📢</div>
      <div class="stat-number" id="statActu">{summary.get("actualites", 0)}</div>
      <div class="stat-label">Actualités</div>
    </div>
  </div>

  <!-- FILTER BAR -->
  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterItems('all', this)">Tous</button>
    <button class="filter-btn" onclick="filterItems('new', this)">🆕 Nouveaux seulement</button>
    <button class="filter-btn" onclick="filterItems('avis_publics', this)">📋 Avis publics</button>
    <button class="filter-btn" onclick="filterItems('calendrier_audiences', this)">🗓️ Audiences</button>
    <button class="filter-btn" onclick="filterItems('decisions', this)">⚖️ Décisions</button>
    <button class="filter-btn" onclick="filterItems('actualites', this)">📢 Actualités</button>
  </div>

  <div class="content-grid">

    <!-- MAIN CONTENT -->
    <div>
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">
            📋 Avis publics
            <span id="badgeAvis" class="new-badge" style="display:none"></span>
          </span>
        </div>
        <div class="panel-body" id="sectionAvis"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">
            🗓️ Calendrier des audiences
            <span id="badgeAudience" class="new-badge" style="display:none"></span>
          </span>
        </div>
        <div class="panel-body" id="sectionAudience"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">
            ⚖️ Décisions rendues
            <span id="badgeDecision" class="new-badge" style="display:none"></span>
          </span>
        </div>
        <div class="panel-body" id="sectionDecision"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">
            📢 Actualités & dossiers prioritaires
            <span id="badgeActu" class="new-badge" style="display:none"></span>
          </span>
        </div>
        <div class="panel-body" id="sectionActu"></div>
      </div>
    </div>

    <!-- SIDEBAR -->
    <div>
      <div class="sidebar-panel">
        <div class="sidebar-header">🔍 Recherche</div>
        <div class="sidebar-body">
          <input type="text" class="search-input" id="searchInput" placeholder="Rechercher un transporteur, territoire..." oninput="searchItems(this.value)">
        </div>
      </div>

      <div class="sidebar-panel">
        <div class="sidebar-header">📈 Activité (30 jours)</div>
        <div class="sidebar-body">
          <div class="chart-container">
            <div class="chart-bars" id="historyChart"></div>
            <div class="chart-labels" id="historyLabels"></div>
          </div>
        </div>
      </div>

      <div class="sidebar-panel">
        <div class="sidebar-header">🏷️ Filtrer par tag</div>
        <div class="sidebar-body" id="tagCloud"></div>
      </div>

      <!-- LOOKUP DÉTENTEURS -->
      <div class="sidebar-panel" style="border:1px solid rgba(232,75,28,0.35);">
        <div class="sidebar-header" style="background:rgba(232,75,28,0.12);color:#ff7f5c;">🔎 Lookup détenteur de permis</div>
        <div class="sidebar-body">
          <div style="font-size:11px;color:var(--muted);margin-bottom:10px;line-height:1.5;">
            Entrer un nom de transporteur — le nom sera <strong style="color:var(--text)">copié automatiquement</strong> dans le presse-papier avant l'ouverture du portail CTQ.
          </div>

          <div style="position:relative;margin-bottom:10px;">
            <input type="text" id="lookupInput"
              placeholder="Ex: Autobus Ménard, Groupe Rive-Nord..."
              style="width:100%;background:var(--dark3);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:8px 10px;font-size:12px;font-family:'DM Sans',sans-serif;outline:none;box-sizing:border-box;"
              oninput="updateLookupLinks(this.value)"
            >
            <span id="copiedBadge" style="display:none;position:absolute;right:8px;top:50%;transform:translateY(-50%);background:#10B981;color:white;font-size:9px;font-weight:700;padding:2px 6px;border-radius:3px;">✓ COPIÉ</span>
          </div>

          <div style="display:grid;gap:6px;">

            <button onclick="launchPortal('https://www.pes.ctq.gouv.qc.ca/pes2/mvc/dossierclient?voletContexte=RECHERCHE_GLOBAL_MENU', 'Nom du transporteur')"
              style="display:flex;align-items:center;gap:8px;background:rgba(232,75,28,0.1);border:1px solid rgba(232,75,28,0.25);border-radius:6px;padding:9px 10px;cursor:pointer;color:var(--text);font-size:11px;font-weight:600;text-align:left;width:100%;transition:background 0.2s;"
              onmouseover="this.style.background='rgba(232,75,28,0.22)'" onmouseout="this.style.background='rgba(232,75,28,0.1)'">
              <span style="font-size:15px;">🏢</span>
              <div style="flex:1;"><div style="color:#ff7f5c;">Dossier entreprise / individu</div><div style="font-size:10px;color:var(--muted);margin-top:1px;">Tous permis du détenteur — champ «Nom»</div></div>
              <span style="color:var(--muted);font-size:13px;">↗</span>
            </button>

            <button onclick="launchPortal('https://www.pes.ctq.gouv.qc.ca/pes2/mvc/permisautobus?voletContexte=RECHERCHE_AUTOBUS_NOLISE_MENU', 'Titulaire')"
              style="display:flex;align-items:center;gap:8px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);border-radius:6px;padding:9px 10px;cursor:pointer;color:var(--text);font-size:11px;font-weight:600;text-align:left;width:100%;transition:background 0.2s;"
              onmouseover="this.style.background='rgba(59,130,246,0.22)'" onmouseout="this.style.background='rgba(59,130,246,0.1)'">
              <span style="font-size:15px;">🚌</span>
              <div style="flex:1;"><div style="color:#60a5fa;">Permis nolisé — carte interactive</div><div style="font-size:10px;color:var(--muted);margin-top:1px;">Territoires desservis — champ «Titulaire»</div></div>
              <span style="color:var(--muted);font-size:13px;">↗</span>
            </button>

            <a href="https://www.ctq.gouv.qc.ca/securite-routiere/proprietaires-et-exploitants-de-vehicules-lourds/inscription-au-registre-nir-et-cote-de-securite/" target="_blank"
              style="display:flex;align-items:center;gap:8px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:6px;padding:9px 10px;text-decoration:none;color:var(--text);font-size:11px;font-weight:600;transition:background 0.2s;"
              onmouseover="this.style.background='rgba(16,185,129,0.22)'" onmouseout="this.style.background='rgba(16,185,129,0.1)'">
              <span style="font-size:15px;">🛡️</span>
              <div style="flex:1;"><div style="color:#34d399;">NIR &amp; cote de sécurité</div><div style="font-size:10px;color:var(--muted);margin-top:1px;">Inscription, cote, réévaluation</div></div>
              <span style="color:var(--muted);font-size:13px;">↗</span>
            </a>

            <a href="https://www.ctq.gouv.qc.ca/securite-routiere/proprietaires-et-exploitants-de-vehicules-lourds/registre-des-proprietaires-et-des-exploitants-de-vehicules-lourds/" target="_blank"
              style="display:flex;align-items:center;gap:8px;background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.25);border-radius:6px;padding:9px 10px;text-decoration:none;color:var(--text);font-size:11px;font-weight:600;transition:background 0.2s;"
              onmouseover="this.style.background='rgba(139,92,246,0.22)'" onmouseout="this.style.background='rgba(139,92,246,0.1)'">
              <span style="font-size:15px;">📋</span>
              <div style="flex:1;"><div style="color:#a78bfa;">Registre RPEVL</div><div style="font-size:10px;color:var(--muted);margin-top:1px;">Propriétaires et exploitants de véhicules lourds</div></div>
              <span style="color:var(--muted);font-size:13px;">↗</span>
            </a>

            <a href="https://www.ctq.gouv.qc.ca/permis-et-autorisations-de-transport/autobus/permis/" target="_blank"
              style="display:flex;align-items:center;gap:8px;background:rgba(251,146,60,0.1);border:1px solid rgba(251,146,60,0.25);border-radius:6px;padding:9px 10px;text-decoration:none;color:var(--text);font-size:11px;font-weight:600;transition:background 0.2s;"
              onmouseover="this.style.background='rgba(251,146,60,0.22)'" onmouseout="this.style.background='rgba(251,146,60,0.1)'">
              <span style="font-size:15px;">📄</span>
              <div style="flex:1;"><div style="color:#fb923c;">Info permis d'autobus</div><div style="font-size:10px;color:var(--muted);margin-top:1px;">Catégories, transfert, renouvellement, révocation</div></div>
              <span style="color:var(--muted);font-size:13px;">↗</span>
            </a>

          </div>

          <!-- Toast de confirmation -->
          <div id="lookupToast" style="display:none;margin-top:10px;border-radius:6px;padding:8px 10px;font-size:11px;line-height:1.5;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.3);color:#34d399;">
            ✅ <strong id="toastName" style="color:white;"></strong> copié dans le presse-papier<br>
            <span style="color:var(--muted);">Coller dans le champ <strong id="toastField" style="color:#34d399;"></strong> du portail CTQ</span>
          </div>
        </div>
      </div>

      <!-- RSS READER -->
      <div class="sidebar-panel">
        <div class="sidebar-header" style="flex-direction:column;align-items:flex-start;gap:8px;">
          <span>📡 Avis publics en direct</span>
          <div style="display:flex;gap:5px;flex-wrap:wrap;">
            <button class="rss-tab active" onclick="loadFeed('AUTOBUS','🚌 Autobus',this)" style="font-size:10px;font-weight:600;padding:3px 9px;border-radius:4px;border:1px solid rgba(232,75,28,.4);background:rgba(232,75,28,.15);color:#ff7f5c;cursor:pointer;">🚌 Autobus</button>
            <button class="rss-tab" onclick="loadFeed('COURTAGE','📋 Courtage',this)" style="font-size:10px;font-weight:600;padding:3px 9px;border-radius:4px;border:1px solid var(--border);background:var(--dark3);color:var(--muted2);cursor:pointer;">📋 Courtage</button>
            <button class="rss-tab" onclick="loadFeed('FERROVIAIR','🚂 Ferrov.',this)" style="font-size:10px;font-weight:600;padding:3px 9px;border-radius:4px;border:1px solid var(--border);background:var(--dark3);color:var(--muted2);cursor:pointer;">🚂 Ferrov.</button>
            <button class="rss-tab" onclick="loadFeed('ERRATUM','🔔 Erratum',this)" style="font-size:10px;font-weight:600;padding:3px 9px;border-radius:4px;border:1px solid var(--border);background:var(--dark3);color:var(--muted2);cursor:pointer;">🔔 Erratum</button>
          </div>
        </div>
        <div class="sidebar-body" style="padding:0">
          <div id="rssFeedTitle" style="font-size:10px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;padding:10px 14px 0;"></div>
          <div id="rssFeed" style="max-height:340px;overflow-y:auto;padding:6px 10px 10px;">
            <div style="color:var(--muted);font-size:12px;padding:16px;text-align:center;">Chargement...</div>
          </div>
          <div style="border-top:1px solid var(--border);padding:8px 14px;display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:10px;color:var(--muted)">Source: pes.ctq.gouv.qc.ca</span>
            <a id="rssDirectLink" href="#" target="_blank" style="font-size:10px;color:var(--muted2);text-decoration:none;">XML brut ↗</a>
          </div>
        </div>
      </div>

      <!-- LIENS CTQ -->
      <div class="sidebar-panel">
        <div class="sidebar-header">🔗 Portails CTQ</div>
        <div class="sidebar-body" style="display:grid;gap:5px;">
          <a href="https://www.ctq.gouv.qc.ca/la-commission/laudience/" target="_blank" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:6px;background:var(--dark3);border:1px solid var(--border);text-decoration:none;color:var(--text);font-size:11px;font-weight:500;transition:background .15s" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='var(--dark3)'">🗓️ <span>Calendrier des audiences</span></a>
          <a href="https://www.ctq.gouv.qc.ca/services-en-ligne/recherche-de-decisions/" target="_blank" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:6px;background:var(--dark3);border:1px solid var(--border);text-decoration:none;color:var(--text);font-size:11px;font-weight:500;transition:background .15s" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='var(--dark3)'">⚖️ <span>Recherche de décisions</span></a>
          <a href="https://www.ctq.gouv.qc.ca/actualites-et-dossiers-prioritaires/" target="_blank" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:6px;background:var(--dark3);border:1px solid var(--border);text-decoration:none;color:var(--text);font-size:11px;font-weight:500;transition:background .15s" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='var(--dark3)'">📢 <span>Actualités & dossiers</span></a>
          <a href="https://www.ctq.gouv.qc.ca/permis-et-autorisations-de-transport/autobus/permis/" target="_blank" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:6px;background:var(--dark3);border:1px solid var(--border);text-decoration:none;color:var(--text);font-size:11px;font-weight:500;transition:background .15s" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='var(--dark3)'">🚌 <span>Info permis autobus</span></a>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const ALL_ITEMS = {items_json};
const HISTORY = {history_json};
const SUMMARY = {summary_json};

const TAG_COLORS = {{
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
  "VFÉ": "#2ECC71"
}};

const SECTION_COLORS = {{
  avis_publics: "var(--avis)",
  calendrier_audiences: "var(--audience)",
  decisions: "var(--decision)",
  actualites: "var(--actu)"
}};

let currentFilter = "all";
let currentSearch = "";
let currentTag = "";

function renderTag(tag) {{
  const color = TAG_COLORS[tag] || "#666";
  return `<span class="tag" style="background:${{color}}">${{tag}}</span>`;
}}

function renderItem(item) {{
  const sectionClass = `section-${{item.section.replace("_","-").replace("calendrier-audiences","audience")
    .replace("avis-publics","avis").replace("actualites","actu")}}`;
  const isNew = item.is_new ? "new-item" : "";
  const newBadge = item.is_new ? `<span style="background:#E84B1C;color:white;font-size:9px;font-weight:800;padding:1px 6px;border-radius:2px;margin-left:6px;">NOUVEAU</span>` : "";
  const tags = (item.tags || []).map(renderTag).join(" ");
  const desc = item.description ? `<div class="item-desc">${{item.description.substring(0,180)}}</div>` : "";
  
  return `
    <div class="item-card ${{sectionClass}} ${{isNew}}" data-section="${{item.section}}" data-new="${{item.is_new}}" data-text="${{(item.title+' '+(item.description||'')+' '+(item.tags||[]).join(' ')).toLowerCase()}}">
      <div class="item-title">${{item.icon || ''}} ${{item.title}} ${{newBadge}}</div>
      ${{desc}}
      <div class="item-footer">
        <span class="item-date">📅 ${{item.date_publie}}</span>
        ${{tags}}
        ${{item.url ? `<a href="${{item.url}}" target="_blank" class="item-link">Voir →</a>` : ""}}
      </div>
    </div>
  `;
}}

function renderSection(sectionKey, containerId, badgeId) {{
  const items = ALL_ITEMS.filter(i => i.section === sectionKey);
  const container = document.getElementById(containerId);
  const badge = document.getElementById(badgeId);
  
  if (!items.length) {{
    container.innerHTML = `<div class="empty-state">Aucune activité détectée aujourd'hui</div>`;
    return;
  }}
  
  container.innerHTML = items.map(renderItem).join("");
  const newCount = items.filter(i => i.is_new).length;
  if (newCount > 0) {{
    badge.style.display = "inline";
    badge.textContent = `${{newCount}} nouveau${{newCount > 1 ? "x" : ""}}`;
  }}
}}

function filterItems(filter, btn) {{
  currentFilter = filter;
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  applyFilters();
}}

function searchItems(query) {{
  currentSearch = query.toLowerCase();
  applyFilters();
}}

function filterByTag(tag) {{
  currentTag = currentTag === tag ? "" : tag;
  buildTagCloud();
  applyFilters();
}}

function applyFilters() {{
  document.querySelectorAll(".item-card").forEach(card => {{
    const section = card.dataset.section;
    const isNew = card.dataset.new === "true";
    const text = card.dataset.text;
    
    let show = true;
    if (currentFilter === "new" && !isNew) show = false;
    else if (currentFilter !== "all" && currentFilter !== "new" && section !== currentFilter) show = false;
    if (currentSearch && !text.includes(currentSearch)) show = false;
    if (currentTag && !text.includes(currentTag.toLowerCase())) show = false;
    
    card.style.display = show ? "block" : "none";
  }});
}}

function buildHistoryChart() {{
  const chart = document.getElementById("historyChart");
  const labels = document.getElementById("historyLabels");
  if (!HISTORY.length) return;
  
  const maxVal = Math.max(...HISTORY.map(r => r.new_count), 1);
  
  chart.innerHTML = HISTORY.map(r => {{
    const h = Math.max(4, Math.round((r.new_count / maxVal) * 76));
    const color = r.new_count > 0 ? "#E84B1C" : "#2a2a3e";
    return `<div class="bar" style="height:${{h}}px;background:${{color}};" title="${{r.date}}: ${{r.new_count}} nouveau(x)"></div>`;
  }}).join("");
  
  if (HISTORY.length >= 2) {{
    const first = HISTORY[0].date?.substring(5) || "";
    const last = HISTORY[HISTORY.length-1].date?.substring(5) || "";
    labels.innerHTML = `<span class="chart-label">${{first}}</span><span class="chart-label">${{last}}</span>`;
  }}
}}

function buildTagCloud() {{
  const tagCounts = {{}};
  ALL_ITEMS.forEach(item => {{
    (item.tags || []).forEach(tag => {{
      tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    }});
  }});
  
  const cloud = document.getElementById("tagCloud");
  cloud.innerHTML = Object.entries(tagCounts)
    .sort((a,b) => b[1]-a[1])
    .map(([tag, count]) => {{
      const color = TAG_COLORS[tag] || "#666";
      const active = currentTag === tag ? "outline:2px solid white;" : "";
      return `<span class="tag" style="background:${{color}};cursor:pointer;margin:3px;padding:4px 8px;font-size:10px;${{active}}" onclick="filterByTag('${{tag}}')">${{tag}} (${{count}})</span>`;
    }}).join(" ");
}}

// ── LOOKUP DÉTENTEUR ────────────────────────────────────────────────────────
function updateLookupLinks(query) {{
  const hint = document.getElementById('lookupHint');
  const term = document.getElementById('lookupTerm');
  const q = query.trim();

  if (q.length >= 2) {{
    hint.style.display = 'block';
    term.textContent = q;

    // Construire les URLs avec paramètre de recherche pré-rempli
    // Le portail PES ne supporte pas les query params directs — on affiche le nom à chercher
    const base = 'https://www.pes.ctq.gouv.qc.ca/pes2/mvc/';
    document.getElementById('lnkDossier').href = base + 'dossierclient?voletContexte=RECHERCHE_GLOBAL_MENU';
    document.getElementById('lnkPermisNolise').href = base + 'permisautobus?voletContexte=RECHERCHE_AUTOBUS_NOLISE_MENU';
    document.getElementById('lnkCote').href = base + 'registrecote';
    document.getElementById('lnkAttestation').href = base + 'dossierclient?voletContexte=RECHERCHE_RESTREINT_NIR_FR_MENU';

    // Animation sur les boutons
    document.querySelectorAll('#lookupLinks a').forEach(a => {{
      a.style.transform = 'scale(1.01)';
      setTimeout(() => a.style.transform = '', 200);
    }});
  }} else {{
    hint.style.display = 'none';
  }}
}}

// Clic sur item → pre-fill lookup
document.addEventListener('click', function(e) {{
  const card = e.target.closest('.item-card');
  if (card) {{
    const titleEl = card.querySelector('.item-title');
    if (titleEl) {{
      // Extraire le nom du transporteur (avant le premier tiret)
      const full = titleEl.textContent.trim();
      const parts = full.split('—');
      const transporteur = parts.length > 1 ? parts[parts.length - 1].trim().replace('NOUVEAU','').trim() : '';
      if (transporteur.length > 3) {{
        const input = document.getElementById('lookupInput');
        input.value = transporteur.substring(0, 60);
        updateLookupLinks(input.value);
        input.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        input.style.borderColor = 'var(--red)';
        setTimeout(() => input.style.borderColor = 'var(--border)', 2000);
      }}
    }}
  }}
}});

// ── RSS READER ───────────────────────────────────────────────────────────────
let currentFeed = 'AUTOBUS';

async function loadFeed(feed, label, tabEl) {{
  currentFeed = feed;
  const url = `https://www.pes.ctq.gouv.qc.ca/rss/${{feed}}.xml`;
  document.getElementById('rssDirectLink').href = url;
  document.getElementById('rssFeedTitle').textContent = label;
  document.getElementById('rssFeed').innerHTML = '<div style="color:var(--muted);font-size:12px;padding:16px 6px;text-align:center;">⏳ Chargement...</div>';

  // Update tab styles
  document.querySelectorAll('.rss-tab').forEach(t => {{
    t.style.background = 'var(--dark3)';
    t.style.color = 'var(--muted2)';
    t.style.borderColor = 'var(--border)';
  }});
  if (tabEl) {{
    tabEl.style.background = 'rgba(232,75,28,.15)';
    tabEl.style.color = '#ff7f5c';
    tabEl.style.borderColor = 'rgba(232,75,28,.4)';
  }}

  try {{
    // Use allorigins proxy to bypass CORS
    const proxy = `https://api.allorigins.win/get?url=${{encodeURIComponent(url)}}`;
    const res = await fetch(proxy, {{ signal: AbortSignal.timeout(10000) }});
    const json = await res.json();
    const xml = new DOMParser().parseFromString(json.contents, 'text/xml');
    const items = xml.querySelectorAll('item');

    if (!items.length) {{
      document.getElementById('rssFeed').innerHTML = '<div style="color:var(--muted);font-size:12px;padding:16px 6px;text-align:center;">Aucun avis actif</div>';
      return;
    }}

    let html = '';
    items.forEach(item => {{
      const title = item.querySelector('title')?.textContent || '';
      const link = item.querySelector('link')?.textContent || '#';
      const desc = item.querySelector('description')?.textContent || '';
      const pub = item.querySelector('pubDate')?.textContent || '';

      // Parse description: strip HTML tags, extract key fields
      const clean = desc.replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '').trim();
      const lines = clean.split('\n').map(l => l.trim()).filter(l => l.length > 2);

      // Extract structured fields
      let demandeur = '', noPermis = '', typePermis = '', dateIntro = '';
      lines.forEach(l => {{
        if (l.startsWith('Numéro de la demande')) noPermis = l.replace('Numéro de la demande :', '').trim();
        if (l.startsWith('Date d\'introduction')) dateIntro = l.replace('Date d\'introduction :', '').trim();
        if (l.match(/^[A-Z][A-Z\s\.]+INC\.|LTÉE|ENRG\.|TRANSPORT|AUTOBUS|GROUPE/)) demandeur = l;
        if (l.includes('permis') || l.includes('Permis') || l.includes('nolisé') || l.includes('Maintien')) typePermis = l;
      }});

      const dateStr = pub ? new Date(pub).toLocaleDateString('fr-CA', {{day:'numeric',month:'short',year:'numeric'}}) : '';

      // Detect type for color coding
      let tagColor = '#6b7280', tagLabel = '';
      const titleLow = title.toLowerCase() + clean.toLowerCase();
      if (titleLow.includes('nolisé') || titleLow.includes('nolise')) {{ tagColor = '#E84B1C'; tagLabel = 'Nolisé'; }}
      else if (titleLow.includes('scolaire') || titleLow.includes('élèves')) {{ tagColor = '#3B82F6'; tagLabel = 'Scolaire'; }}
      else if (titleLow.includes('interurbain')) {{ tagColor = '#8B5CF6'; tagLabel = 'Interurbain'; }}
      else if (titleLow.includes('urbain')) {{ tagColor = '#10B981'; tagLabel = 'Urbain'; }}
      else if (titleLow.includes('courtage')) {{ tagColor = '#D97706'; tagLabel = 'Courtage'; }}
      else if (titleLow.includes('ferroviaire')) {{ tagColor = '#6366F1'; tagLabel = 'Ferroviaire'; }}
      else if (titleLow.includes('erratum')) {{ tagColor = '#F59E0B'; tagLabel = 'Erratum'; }}
      else if (titleLow.includes('maintien') || titleLow.includes('acquisition')) {{ tagColor = '#8B5CF6'; tagLabel = 'Maintien'; }}

      // Detect movement type
      let mvLabel = '', mvColor = '#6b7280';
      if (titleLow.includes('maintien') || titleLow.includes('acquisition d\'intérêts') || titleLow.includes('transfert')) {{ mvLabel = 'Transfert'; mvColor = '#8B5CF6'; }}
      else if (titleLow.includes('nouveau') || typePermis.includes('Demande')) {{ mvLabel = 'Nouveau'; mvColor = '#E84B1C'; }}
      else if (titleLow.includes('modification')) {{ mvLabel = 'Modif.'; mvColor = '#3B82F6'; }}
      else if (titleLow.includes('révocation') || titleLow.includes('revocation')) {{ mvLabel = 'Révocation'; mvColor = '#EF4444'; }}

      html += `
        <div style="border:1px solid var(--border);border-left:3px solid ${{tagColor}};border-radius:7px;padding:10px 12px;margin-bottom:7px;background:var(--dark3);cursor:pointer;transition:border-color .15s"
          onmouseover="this.style.borderColor='rgba(255,255,255,.15)'" onmouseout="this.style.borderTopColor=this.style.borderRightColor=this.style.borderBottomColor='var(--border)'">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:5px">
            <div style="font-size:11px;font-weight:700;color:var(--text);line-height:1.3;flex:1">${{demandeur || (lines[0]||'Demandeur').substring(0,50)}}</div>
            <div style="font-size:9px;color:var(--muted);white-space:nowrap">${{dateStr}}</div>
          </div>
          ${{typePermis ? `<div style="font-size:11px;color:var(--muted2);margin-bottom:6px;line-height:1.35">${{typePermis.substring(0,90)}}${{typePermis.length>90?'…':''}}</div>` : ''}}
          ${{noPermis ? `<div style="font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);margin-bottom:6px;">Demande #${{noPermis}}</div>` : ''}}
          <div style="display:flex;gap:4px;flex-wrap:wrap;align-items:center">
            ${{tagLabel ? `<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding:2px 6px;border-radius:3px;background:${{tagColor}}22;color:${{tagColor}}">${{tagLabel}}</span>` : ''}}
            ${{mvLabel ? `<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding:2px 6px;border-radius:3px;background:${{mvColor}}22;color:${{mvColor}}">${{mvLabel}}</span>` : ''}}
            <a href="${{link}}" target="_blank" style="margin-left:auto;font-size:10px;color:var(--muted2);text-decoration:none;padding:2px 6px;border:1px solid var(--border);border-radius:3px;transition:color .15s" onmouseover="this.style.color='var(--text)'" onmouseout="this.style.color='var(--muted2)'">Voir ↗</a>
          </div>
        </div>`;
    }});

    document.getElementById('rssFeed').innerHTML = html;

  }} catch(e) {{
    document.getElementById('rssFeed').innerHTML = `
      <div style="color:var(--muted);font-size:11px;padding:12px 6px;text-align:center;line-height:1.6">
        ⚠️ Impossible de charger le flux en direct.<br>
        <a href="https://www.pes.ctq.gouv.qc.ca/rss/${{currentFeed}}.xml" target="_blank" style="color:var(--red2);">Ouvrir le flux XML ↗</a>
      </div>`;
  }}
}}

// Init RSS on load
loadFeed('AUTOBUS', '🚌 Autobus', document.querySelector('.rss-tab'));

// Init
renderSection("avis_publics", "sectionAvis", "badgeAvis");
renderSection("calendrier_audiences", "sectionAudience", "badgeAudience");
renderSection("decisions", "sectionDecision", "badgeDecision");
renderSection("actualites", "sectionActu", "badgeActu");
buildHistoryChart();
buildTagCloud();
</script>
</body>
</html>"""


def generate_dashboard():
    report = load_latest_report()
    history = load_history()
    html = build_dashboard(report, history)
    output_path = os.path.join(DOCS_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Dashboard généré: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_dashboard()
