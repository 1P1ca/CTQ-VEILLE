# CTQ Veille 🚌

**Rapport quotidien automatisé — Commission des transports du Québec**  
Développé par 1+1 Discovery pour la veille concurrentielle en transport par autobus au Québec.

---

## 🎯 Objectif

Surveiller en temps réel les 4 sections dynamiques du site [ctq.gouv.qc.ca](https://www.ctq.gouv.qc.ca) et livrer chaque matin à **7h30** un rapport personnalisé à Nancy M. :

| Section surveillée | Signal concurrentiel |
|---|---|
| 📋 **Avis publics** | Nouvelles demandes de permis, transferts, modifications de territoire |
| 🗓️ **Calendrier des audiences** | Audiences à venir, parties impliquées |
| ⚖️ **Décisions rendues** | Permis accordés/refusés, révocations, sanctions |
| 📢 **Actualités & dossiers prioritaires** | Changements réglementaires, indexation tarifaire, VFÉ 2030 |

---

## 🏗️ Architecture

```
ctq-veille/
├── scraper.py              # Scraping des 4 sections CTQ + détection de nouveautés
├── generate_dashboard.py   # Génération du dashboard HTML statique
├── email_report.py         # Envoi du rapport courriel HTML
├── run_daily.py            # Orchestrateur principal
├── requirements.txt        # Dépendances Python
├── data/
│   ├── known_hashes.json   # Hashes des éléments déjà vus (diff engine)
│   ├── latest_report.json  # Dernier rapport généré
│   └── report_YYYY-MM-DD.json  # Historique des rapports
├── docs/
│   └── index.html          # Dashboard GitHub Pages
└── .github/workflows/
    └── daily.yml           # GitHub Actions — 7h30 AM Montréal, Lun–Ven
```

---

## 🚀 Mise en place (15 minutes)

### Étape 1 — Créer le repo GitHub

```bash
# Cloner ce projet dans un nouveau repo GitHub (privé recommandé)
git init ctq-veille
cd ctq-veille
git remote add origin https://github.com/VOTRE_ORG/ctq-veille.git
```

### Étape 2 — Configurer GitHub Secrets

Dans **Settings → Secrets and variables → Actions**, ajouter :

| Secret | Valeur | Description |
|--------|--------|-------------|
| `SMTP_HOST` | `smtp.gmail.com` | Serveur SMTP |
| `SMTP_PORT` | `587` | Port SMTP (TLS) |
| `SMTP_USER` | `votre@gmail.com` | Adresse d'envoi |
| `SMTP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Mot de passe d'application Gmail* |
| `RECIPIENT_EMAIL` | `nancy@groupemenard.com` | Destinataire du rapport |

> **Gmail App Password** : Aller dans [myaccount.google.com](https://myaccount.google.com) → Sécurité → Validation en 2 étapes → Mots de passe des applications → Créer un mot de passe pour "CTQ Veille"

### Étape 3 — Activer GitHub Pages

Dans **Settings → Pages** :
- Source : `Deploy from a branch`
- Branch : `gh-pages` / `/ (root)`

Le dashboard sera accessible à :  
`https://VOTRE_ORG.github.io/ctq-veille/`

### Étape 4 — Initialiser les données

```bash
# Installer les dépendances
pip install -r requirements.txt

# Premier run (local) pour créer les fichiers de base
python run_daily.py
```

### Étape 5 — Activer les workflows GitHub Actions

Dans **Actions → Enable workflows**

---

## ⚙️ Configuration du calendrier

Le workflow tourne **du lundi au vendredi à 7h30 AM heure de Montréal**.

Pour modifier la fréquence, éditer `.github/workflows/daily.yml` :

```yaml
# Tous les jours (incluant week-end) à 7h30
- cron: "30 11 * * *"

# Deux fois par jour (matin + midi)
- cron: "30 11,16 * * 1-5"
```

---

## 🔄 Déclenchement manuel

Aller dans **Actions → CTQ Veille — Rapport Quotidien → Run workflow**

Option disponible : `force_all_new = true` pour re-marquer tous les éléments comme nouveaux (utile pour un premier envoi complet).

---

## 📊 Dashboard

Le dashboard HTML est généré automatiquement à chaque run et déployé sur GitHub Pages. Il offre :

- Compteurs par section (nouveaux éléments du jour)
- Filtres par section, tag, et recherche textuelle
- Graphique historique des 30 derniers jours
- Accès direct aux liens CTQ

---

## 🏷️ Tags automatiques

Le système détecte automatiquement les tags suivants dans le contenu :

`Nouveau permis` · `Transfert` · `Modification territoire` · `Nolisé` · `Transport scolaire` · `Révocation` · `Interurbain` · `Urbain` · `Audience` · `Tarification` · `VFÉ`

---

## 📁 Données historiques

Chaque rapport quotidien est sauvegardé dans `data/report_YYYY-MM-DD.json` et commité automatiquement dans le repo. L'historique complet est ainsi conservé dans Git.

---

## ⚠️ Notes importantes

- Le site CTQ **ne dispose pas d'API ni de flux RSS** — le scraping s'appuie sur l'analyse HTML des pages publiques
- En cas de modification de la structure HTML du site CTQ, les sélecteurs du `scraper.py` devront être ajustés
- Le scraper respecte un délai de 2 secondes entre chaque requête pour ne pas surcharger le serveur

---

*Développé par [1+1 Discovery](https://1p1.ca) — Montréal, Québec*
