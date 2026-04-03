# Pipeline d'Inférence en Production

Solution modulaire pour générer des prédictions sur 3 jours stockées en base de données PostgreSQL.

## 📁 Structure des fichiers

### Modules Python (`utils/`)

- **`inference_model.py`** - Gestion du chargement et utilisation du modèle depuis MLflow
- **`data_generator.py`** - Génération de données d'inférence pour 3 jours
- **`database_handler.py`** - Gestion de la base de données PostgreSQL avec SQLAlchemy
- **`prediction_pipeline.py`** - Pipeline complet orchestrant les étapes

### Notebook

- **`04_Production_Inference_3Days_Predictions.ipynb`** - Notebook d'exécution du pipeline

## 🚀 Utilisation

### 1. Configuration des paramètres

Dans le notebook, adapter les variables:

```python
MLFLOW_TRACKING_URI = "https://jenedai-mlflow.hf.space/"
MODEL_NAME = "enedis_model"  # Modèle à charger
DB_USER = "postgres"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "mlops_db"
```

### 2. Exécuter le pipeline

```python
from utils.prediction_pipeline import PredictionPipeline

pipeline = PredictionPipeline(
    mlflow_uri=MLFLOW_TRACKING_URI,
    experiment_name="enedis_project",
    db_uri=DB_URI
)

# Exécuter le pipeline complet
success, predictions_df = pipeline.run_full_pipeline(
    model_name=MODEL_NAME,
    feature_columns=FEATURE_COLUMNS,
    n_days=3,
    n_samples_per_day=24
)
```

## 📦 Dépendances requises

```
mlflow
sqlalchemy
psycopg2-binary
pandas
numpy
scikit-learn
```

## 🔄 Étapes du pipeline

1. **Setup** - Initialise MLflow et la base de données
2. **Chargement du modèle** - Récupère le modèle en Production depuis MLflow
3. **Génération des données** - Crée 3 jours de données (72 échantillons hourly par défaut)
4. **Prédictions** - Exécute l'inférence avec scores de confiance
5. **Stockage BD** - Sauvegarde les prédictions en PostgreSQL
6. **Vérification** - Affiche les statistiques et derniers résultats

## 📊 Structure de la table `predictions`

```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT,
    model_version VARCHAR,
    created_at DATETIME DEFAULT NOW()
)
```

## 🔧 Utilisation avancée

### Générer les données personnalisées

```python
from utils.data_generator import generate_inference_data

df_data = generate_inference_data(
    n_days=3,
    n_samples_per_day=24,
    feature_columns=['temperature', 'humidity', 'wind_speed'],
    seed=42
)
```

### Interroger les prédictions stockées

```python
from utils.database_handler import DatabaseHandler

db = DatabaseHandler(db_uri)
recent = db.get_recent_predictions(limit=100)
print(recent)
```

## 📝 Notes

- Pas de support SQLite (PostgreSQL uniquement)
- Le modèle est chargé depuis MLflow en Production
- Les données d'inférence sont générées aléatoirement (à adapter avec vos vraies données)
- Tous les logs sont affichés dans le notebook pour la traçabilité

## ⚠️ Améliorations possibles

- Remplacer la génération aléatoire de données par un chargement depuis une API/source réelle
- Ajouter des métriques de validation des prédictions
- Implémenter un système de retry en cas d'erreur BD
- Paralléliser les prédictions pour optimiser la performance
