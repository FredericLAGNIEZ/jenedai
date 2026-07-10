<<<<<<< HEAD
# jenedai
repo pour le projet principal Jedha
=======
# Jenedai - Plateforme MLOps de Prévision de Consommation Électrique

## 🎯 Objectif

Plateforme de **collecte automatisée**, **traitement** et **prévision** de données de consommation électrique basée sur les données ouvertes Enedis avec un pipeline MLOps complet en production.

- **Prévision** : J+5 jours avec recalcul automatique en cas d'écart
- **Données** : API REST Enedis Open Data
- **Collecte** : Automatisée via n8n ou Python
- **Infrastructure** : Local ou Hugging Face

---

## 🏗️ Architecture

### Vue d'ensemble

```
┌─────────────────┐
│  Enedis API     │ (Données: consommation)
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │  Collecte            │
    │  n8n / Python        │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  Base de données      │
    │  PostgreSQL / Supabase│
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  ETL / Orchestration  │
    │  Spark / Airflow      │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  Machine Learning     │
    │  Training + Prédiction│
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  ML Tracking & Monitor│
    │  MLFlow + Evidently   │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  Frontend             │
    │  Streamlit / Gradio   │
    └──────────────────────┘
```

---

## 🛠️ Stack Technologique

| Domaine | Technologie | Rôle |
|---------|-------------|------|
| **Conteneurisation** | Docker / Docker Compose | Packaging et déploiement |
| **Orchestration** | Airflow | Orchestration des pipelines | ou Prefect
| **Collecte données** | n8n / Python | Récupération données Enedis |
| **Base de données** | PostgreSQL / Supabase | Stockage données raw et traitées |
| **ETL** | Spark (optionnel) | Transformation des volumes importants |
| **ML Training** | Python (scikit-learn, XGBoost, etc.) | Prévisions électricité J+5 |
| **ML Tracking** | MLFlow | Versioning modèles, hyperparamètres |
| **Monitoring ML** | Evidently AI | Détection drift, qualité modèles |
| **Frontend** | Streamlit / Gradio | Visualisation des prévisions |
| **Source Control** | GitHub | Gestion versions code |
| **CI/CD** | GitHub Actions | Tests et déploiement automatisés |
| **Documentation** | mkdocs | Documentation technique | (optionnel)

---

## 📁 Structure du Projet

```
Jenedai/
├── README.md                  # Ce fichier
├── docker-compose.yml         # Orchestration services
├── .github/
│   ├── workflows/             # CI/CD GitHub Actions
│   └── copilot-instructions.md# Préférences coding
├── K8s/                       # Configs Kubernetes
├── Services/                  # Services conteneurisés
│   ├── AirFlow/               # Orchestrateur pipelines
│   ├── ClickHouse/            # Analyse données (optionnel)
│   ├── EvidentlyAI/           # Monitoring ML
│   ├── JupyterLab/           # Notebooks de développement
│   ├── Gradio/               # Frontend alternative
│   ├── MLflow/               # Tracking ML
│   ├── n8n/                  # Collecte automatisée
│   ├── Streamlit/            # Frontend principal
│   └── PostgreSQL/           # Base de données (dans compose)
└── src/                      # Code Python applicatif
    ├── __init__.py
    ├── data/                 # Scripts collecte / ETL
    ├── models/               # Pipelines ML
    ├── monitoring/           # Scripts monitoring
    └── utils/                # Utilitaires
```

---

## ⚡ Démarrage Rapide

### Prérequis

- Docker & Docker Compose
- Python 3.10+
- Git

### Installation & Lancement

```bash
# Cloner le repository
git clone https://github.com/username/Jenedai.git
cd Jenedai

# Démarrer tous les services
docker-compose up -d

# Accès aux services (A configurer)
- Streamlit:    http://localhost:8501
- Airflow:      http://localhost:8080
- MLflow:       http://localhost:5000
- JupyterLab:   http://localhost:8888
- Gradio:       http://localhost:7860
- n8n:          http://localhost:5678
```

### Configuration

1. **Variables d'environnement** (.env) (A configurer)
```
# Enedis API
ENEDIS_API_KEY=<votre_clé>
ENEDIS_ENDPOINT=https://data.enedis.fr/api

# PostgreSQL
POSTGRES_USER=mlops
POSTGRES_PASSWORD=<mot_de_passe>
POSTGRES_DB=electricity

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000

# Airflow
AIRFLOW_HOME=/airflow
AIRFLOW__CORE__DAGS_FOLDER=/airflow/dags
```

2. **Base de données** : Migrations PostgreSQL automatisées au démarrage (A préciser)

---

## 🔄 Pipeline MLOps

### Flux de travail (A préciser)

```
1. COLLECTE (Daily)
   └─> n8n trigger → Python script
       └─> Appel API Enedis
           └─> Insertion PostgreSQL

2. TRAITEMENT (Daily)
   └─> Airflow DAG
       ├─> Validation données
       ├─> Nettoyage & enrichissement
       └─> Feature engineering

3. TRAINING (Weekly)
   └─> Airflow DAG
       ├─> Split train/test
       ├─> Entraînement modèle
       ├─> Évaluation
       └─> MLflow logging

4. PRÉDICTION (Daily)
   └─> Airflow DAG
       ├─> Récupération dernier modèle MLflow
       ├─> Prévision J+5
       └─> Stockage résultats

5. MONITORING (Continuous)
   └─> Evidently AI
       ├─> Data drift detection
       ├─> Model performance drift
       └─> Alertes

6. VISUALISATION (Real-time)
   └─> Streamlit / Gradio
       ├─> Prévisions
       ├─> Historique
       └─> Métriques
```

---

## 📊 Services Détaillés

### Airflow
Orchestration des pipelines de données et ML.
- **DAGs** : Collecte, traitement, training, prédiction
- **Dossier** : `Services/AirFlow/dags/`
- [Voir README](Services/AirFlow/README.md)

### PostgreSQL Data Warehouse
Base de données centrale (ou Supabase en cloud).
- **Tables** : raw_consumption, processed_consumption, predictions
- Initialisation automatique via scripts SQL

### n8n
Collecte automatisée depuis API Enedis.
- **Workflows** : Programmation daily, gestion erreurs, retry
- **Alternative** : Scripts Python Python dans `src/data/`
- [Voir README](Services/n8n/README.md)

### MLflow
Tracking des expériences ML et gestion des modèles.
- **Registry** : Versions, staging, production
- **Artifacts** : Modèles, scalers, encoders
- [Voir README](Services/MLflow/README.md)

### Evidently AI
Monitoring continu de la qualité des prévisions.
- **Métriques** : Drift détection, performance dégradation
- **Reports** : Visuels, export HTML
- [Voir README](Services/EvidentlyAI/README.md)

### Streamlit
Interface interactive pour visualiser les prévisions.
- **Pages** : Prévisions, historique, métriques, paramètres
- **Fichier** : `Services/Streamlit/src/streamlit_app.py`
- [Voir README](Services/Streamlit/README.md)

### JupyterLab
Environnement développement avec notebooks.
- **Notebooks** : EDA, tests modèles, debugging
- **Dossier** : `Services/JupyterLab/notebooks/`
- [Voir README](Services/JupyterLab/README.md)

### Gradio (Optionnel)
Alternative légère à Streamlit pour déployer modèles.
- **Fichier** : `Services/Gradio/app.py`
- [Voir README](Services/Gradio/README.md)

---

## 🔐 Authentification & Sécurité (A préciser)

- **API Enedis** : Clé d'accès en variable d'environnement
- **PostgreSQL** : Credentials en .env (non-commité)
- **GitHub Actions** : Secrets pour déploiement
- **MLflow** : Authentification basique (à configurer pour prod)

---

## 📈 Métriques & KPIs (A préciser)

| Métrique | Seuil Alerte | Fréquence Check |
|----------|-------------|-----------------|
| RMSE prévisions | > 15% | Daily |
| Data drift | Wasserstein > 0.1 | Daily |
| Model drift | Accuracy < seuil baseline | Weekly |
| Latence collecte | > 30 min | Per trigger |
| Couverture données | < 90% | Daily |

---

## 🚀 Déploiement

### Local (Développement) (Besoin d'une machine puissante...?)
```bash
docker-compose -f docker-compose.yml up -d
```

### Hugging Face (Space) (Deployement automatique par workflow GitHub Action)
```bash
https://huggingface.co/Jenedai
https://sustcoop-streamlit.hf.space/
```

### Hugging Face Hub (Production) (A voir si interessant)
```bash
# Pusher modèle et artifacts versionnés
huggingface-hub upload Jenedai/electricity-forecast model.pkl dataset.csv
```

### GitHub Actions (CI/CD) (A préciser)
- ✅ Tests unitaires sur PR
- ✅ Build images Docker automatique
- ✅ Push registry
- ✅ Redéploiement services

---

## 📚 Documentation Additionnelle (A préciser)

- [Setup complet](docs/SETUP.md)
- [Guide développeur](docs/DEVELOPER.md)
- [Architecture détaillée](docs/ARCHITECTURE.md)
- [API endpoints](docs/API.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🤝 Contribution (A préciser)

1. Fork le repo
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

---

## 📝 Licence (A préciser)

MIT

---

## 📞 Support (A préciser)

- Issues : GitHub Issues
- Documentation : [mkdocs](http://localhost:8000) après `mkdocs serve`

---

**Dernière mise à jour** : Mars 2026
>>>>>>> bb20d6e (Hugging Face Deployment Workflows)
