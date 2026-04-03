# Utilitaires MLOps - Documentation

## Structure

Le répertoire `utils/` contient tous les modules Python pour le pipeline MLOps simplifié:

```
utils/
├── __init__.py                 # Module init
├── config.yaml                 # Configuration centralisée
├── data_loader.py              # Chargement et préparation des données
├── data_validator.py           # Validation des données (Evidently AI)
├── model.py                    # Entraînement et évaluation du modèle
├── mlflow_tracker.py           # Suivi avec MLflow
├── performance_monitor.py      # Monitoring de performance (Evidently AI)
└── pipeline.py                 # Pipeline complet
```

## Modules

### 1. `data_loader.py`
Gestion du chargement et préparation des données.

```python
from utils.data_loader import load_data, split_data

# Charger les données
data = load_data("data/raw/train.csv")

# Diviser en train/test
X_train, X_test, y_train, y_test = split_data(data, test_size=0.2)
```

### 2. `data_validator.py` (Evidently AI)
Validation de la qualité des données avec rapports Evidently.

```python
from utils.data_validator import validate_data_quality, create_data_validation_report

# Validation basique
results = validate_data_quality(data)

# Rapport Evidently
report = create_data_validation_report(
    current_data=data,
    output_path="outputs/validation_report.html"
)
```

### 3. `model.py`
Entraînement et évaluation du modèle machine learning.

```python
from utils.model import train_model, evaluate_model

# Entraîner
model = train_model(X_train, y_train)

# Évaluer
metrics = evaluate_model(model, X_test, y_test)

# Note: Le modèle est sauvegardé via MLflow (voir step_7_log_with_mlflow)
```

### 4. `mlflow_tracker.py`
Suivi des expériences avec MLflow.

```python
from utils.mlflow_tracker import log_training_session

log_training_session(
    model=model,
    metrics=metrics,
    params={'test_size': 0.2},
    experiment_name="enedis_project"
)
```

### 5. `performance_monitor.py` (Evidently AI)
Monitoring de la performance du modèle et détection de drift.

```python
from utils.performance_monitor import detect_prediction_drift, monitor_model_performance

# Détection de drift
drift = detect_prediction_drift(pred_ref, pred_current)

# Monitoring
perf = monitor_model_performance(y_pred, y_actual)
```

### 6. `pipeline.py`
Pipeline complet intégrant toutes les étapes.

```python
from utils.pipeline import MLPipeline

pipeline = MLPipeline(config_path="utils/config.yaml")
pipeline.run_full_pipeline("data/raw/train.csv")
```

## Configuration

Le fichier `config.yaml` centralise tous les paramètres:

```yaml
data:
  raw_path: "data/raw/"
  processed_path: "data/processed/"
  models_path: "Models/"

model:
  test_size: 0.2
  random_state: 42
  model_type: "random_forest"

mlflow:
  tracking_uri: "http://mlflow:5000"
  experiment_name: "enedis_project"

monitoring:
  reference_data_path: "data/processed/reference.csv"
  dashboard_path: "outputs/evidently_dashboard.html"
```

## Utilisation Rapide

### Approche simple (Notebook)

```python
from utils.data_loader import load_data, split_data
from utils.model import train_model, evaluate_model

# 1. Charger les données
data = load_data("data/raw/enedis.csv")

# 2. Préparer
X_train, X_test, y_train, y_test = split_data(data)

# 3. Entraîner
model = train_model(X_train, y_train)

# 4. Évaluer
metrics = evaluate_model(model, X_test, y_test)
```

### Approche complète (Pipeline)

```python
from utils.pipeline import MLPipeline

pipeline = MLPipeline()
pipeline.run_full_pipeline("data/raw/enedis.csv")
```

## Validation et Monitoring

### Validation des données avec Evidently AI

```python
from utils.data_validator import create_data_validation_report

# Rapport de validation
report = create_data_validation_report(
    current_data=data,
    reference_data=reference_data,  # optionnel
    output_path="outputs/validation_report.html"
)
```

### Monitoring de performance avec Evidently AI

```python
from utils.performance_monitor import create_performance_report

report = create_performance_report(
    reference_data=X_test,
    current_data=X_new,
    predictions_ref=y_pred_ref,
    predictions_current=y_pred_current,
    output_path="outputs/performance_report.html",
    problem_type="classification"
)
```

## Installation des dépendances

```bash
pip install -r requirements_utils.txt
```

## Notes

- Tous les modules utilisent du logging pour la traçabilité
- Les chemins sont configurables via `config.yaml`
- Evidently AI génère des rapports HTML interactifs
- MLflow intègre le suivi des expériences
- Le pipeline peut être utilisé tel quel ou adapté
