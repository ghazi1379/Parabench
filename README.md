# 🧴 ParaBench — Benchmark Marché Parapharmaceutique Tunisien

**ParaBench** est une plateforme professionnelle de surveillance et d'analyse du marché parapharmaceutique tunisien. Elle scrape automatiquement les 3 principaux sites e-commerce para tunisiens et transforme les données en insights business actionnables.

---

## 📸 Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 🏠 **Dashboard** | Vue globale : KPIs, graphiques prix, top marques/catégories |
| 📦 **Catalogue** | 25+ filtres, recherche full-text, pagination |
| 📊 **Benchmark** | Comparateur de prix multi-sites en temps réel |
| 🧠 **Market Intelligence** | Alertes prix, gaps assortiment, évolution marques |
| ⚙️ **Admin Scraping** | Déclenchement manuel + cron automatique + logs live |
| 📤 **Exports** | Excel, CSV, PDF en un clic |

---

## 🏗️ Architecture

```
parabench/
├── backend/                  # FastAPI + SQLAlchemy
│   ├── main.py               # App FastAPI + tous les endpoints
│   ├── models/               # Modèles SQLAlchemy
│   │   ├── models.py         # Product, PriceHistory, ScrapingJob...
│   │   └── database.py       # Connexion PostgreSQL
│   ├── scrapers/             # Moteurs de scraping
│   │   ├── base_scraper.py   # Classe abstraite (Playwright)
│   │   ├── parashop_scraper.py
│   │   ├── parafendri_scraper.py
│   │   ├── tunisiepara_scraper.py
│   │   └── detail_scraper.py # Enrichissement pages produit
│   ├── services/
│   │   ├── scraping_service.py  # Orchestration + upsert DB
│   │   ├── analytics_service.py # Analyses avancées
│   │   ├── export_service.py    # Excel / CSV / PDF
│   │   └── celery_app.py        # Tâches async + cron
│   └── api/
│       ├── schemas.py
│       └── analytics_routes.py
├── frontend/                 # React 18 + Recharts
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.js
│       │   ├── Products.js
│       │   ├── Benchmark.js
│       │   ├── Analytics.js
│       │   └── Admin.js
│       └── utils/
│           ├── api.js        # Axios client
│           └── helpers.js    # Formatage, couleurs
├── database/
│   └── init.sql              # Vues SQL analytiques
├── docker/
│   └── nginx.conf
├── scripts/
│   ├── install.sh            # Installation automatique
│   ├── dev.sh                # Mode développement
│   └── test_scrapers.py      # Test unitaire scrapers
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Installation (5 minutes)

### Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24
- 4 GB de RAM disponible
- Ports libres : 80, 3000, 8000, 5432, 6379

### Installation en une commande

```bash
# 1. Cloner / dézipper le projet
cd parabench

# 2. Lancer l'installation automatique
bash scripts/install.sh
```

C'est tout ! Le script gère tout automatiquement.

### Installation manuelle

```bash
# 1. Configurer l'environnement
cp .env.example .env
# Éditez .env et changez les mots de passe

# 2. Construire et démarrer
docker compose build
docker compose up -d

# 3. Vérifier
curl http://localhost:8000/api/health
```

---

## 🌐 Accès

| Service | URL |
|---|---|
| 🖥️ Application web | http://localhost:3000 |
| ⚙️ API Backend | http://localhost:8000 |
| 📖 Documentation API | http://localhost:8000/docs |
| 🔀 Via Nginx | http://localhost:80 |

---

## 📊 Sites Scrapés

| Site | URL | Technologie |
|---|---|---|
| Parashop | https://www.parashop.tn | PrestaShop |
| Parafendri | https://parafendri.tn | WooCommerce |
| TunisiePara | https://www.tunisiepara.com | PrestaShop |

---

## 🔄 Utilisation

### Lancer le scraping
1. Ouvrir http://localhost:3000
2. Aller dans **Admin & Scraping**
3. Sélectionner les sites souhaités
4. Cliquer sur **"Lancer le Scraping"**
5. Suivre les logs en temps réel

### Scraping automatique
Le scraping s'exécute automatiquement **chaque nuit à 2h00** (configurable dans `.env`).

### Mettre à jour le benchmark
- Automatique après chaque scraping
- Manuel : bouton "Mettre à jour Benchmark" dans Admin

### Exporter les données
- **Products > CSV/Excel/PDF** : export catalogue complet
- **Benchmark > Excel** : export comparatif prix

---

## 📡 API Endpoints

### Dashboard
```
GET /api/dashboard/stats          → KPIs globaux
GET /api/dashboard/top-brands     → Top 10 marques
GET /api/dashboard/top-categories → Top catégories
GET /api/dashboard/promotions     → Promos du moment
GET /api/dashboard/price-evolution → Évolution 30j
```

### Produits
```
GET /api/products                 → Liste paginée (filtres)
GET /api/products/{id}            → Détail + historique prix
GET /api/products/filters/brands  → Liste marques
GET /api/products/filters/categories → Liste catégories
```

### Benchmark
```
GET /api/benchmark                → Comparatif prix
POST /api/benchmark/refresh       → Mise à jour
```

### Analytics
```
GET /api/analytics/market-overview    → Vue marché global
GET /api/analytics/brands             → Analyse marques
GET /api/analytics/price-alerts       → Alertes écarts prix
GET /api/analytics/assortment-gaps    → Gaps assortiment
GET /api/analytics/brand-evolution    → Évolution marque
```

### Scraping
```
POST /api/scraping/start          → Lancer scraping
GET  /api/scraping/jobs           → Historique jobs
GET  /api/scraping/status         → Statut en cours
GET  /api/scraping/logs/{job_id}  → Logs d'un job
```

### Exports
```
GET /api/export/csv
GET /api/export/excel
GET /api/export/pdf
GET /api/export/benchmark/excel
```

---

## 🛠️ Configuration `.env`

| Variable | Description | Défaut |
|---|---|---|
| `POSTGRES_PASSWORD` | Mot de passe DB | À changer |
| `SECRET_KEY` | Clé JWT secrète | À changer |
| `SCRAPING_DELAY_MIN` | Délai min entre requêtes (s) | 1.5 |
| `SCRAPING_DELAY_MAX` | Délai max entre requêtes (s) | 4.0 |
| `SCRAPING_CRON_HOUR` | Heure scraping auto (UTC) | 2 |
| `MAX_RETRIES` | Tentatives en cas d'échec | 3 |

---

## 🐛 Dépannage

### Le backend ne démarre pas
```bash
docker compose logs backend
```

### Playwright / Chromium erreur
```bash
docker compose exec backend playwright install-deps chromium
```

### Base de données inaccessible
```bash
docker compose restart postgres
docker compose logs postgres
```

### Vider et recommencer
```bash
docker compose down -v   # Supprime les données !
docker compose up -d
```

### Tester les scrapers sans Docker
```bash
cd parabench
python3 scripts/test_scrapers.py parashop
python3 scripts/test_scrapers.py all
```

---

## 🔧 Développement

### Mode dev (sans Docker)
```bash
# Démarrer PostgreSQL et Redis localement, puis :
bash scripts/dev.sh
```

### Ajouter un nouveau site
1. Créer `backend/scrapers/monsite_scraper.py` héritant de `BaseScraper`
2. Implémenter `scrape_all_products()` et `scrape_categories()`
3. Ajouter dans `backend/scrapers/__init__.py`
4. Ajouter dans `SiteEnum` dans `models.py`

---

## 📈 Roadmap

- [ ] Alertes email automatiques (prix anormaux)
- [ ] API mobile (React Native)
- [ ] Matching produits par EAN/code-barre
- [ ] OCR labels produits
- [ ] Intégration Google Sheets
- [ ] Mode SaaS multi-tenant

---

## 📄 License

Usage interne — ParaBench est un outil propriétaire de veille concurrentielle.

---

*Développé pour le marché parapharmaceutique tunisien 🇹🇳*
