# Pipeline d'entraînement Jenedai

## Vue d'ensemble

Le pipeline d'entraînement est orchestré via **Prefect** et tracké via **MLflow**.
Il enchaîne chargement → validation → cast → transformation → entraînement → enregistrement.

```
Source (S3 ou BDD)
        │
        ▼
   load_task_s3 / load_task_bdd
        │
        ▼
   validate_task          ← DataValidator
        │
        ▼
   cast_task              ← DataCaster
        │
        ▼
   transform_task         ← Transformer
        │
        ▼
   train                  ← EnergyPredictor + MLflow
        │
        ▼
   register               ← MLflow Model Registry (alias "champion")
```

 load_task_s3 qui charge un dataset inital sur un S3 pour l'entrainement initial.Ce dataset comporte 500000 lignes et a été préparé avec l'outil nocode ...

---

## Sources de données

### `load_task_s3` — Entraînement initial

Charge un dataset statique (~500 000 lignes) depuis le bucket S3 Garage :

- **Bucket** : `jenedai`
- **Fichier** : `dataset_train.csv`
- **Endpoint** : `https://garage.learndatascience.cloud`

Variables d'environnement requises (dans `.env`) :

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
MLFLOW_S3_ENDPOINT_URL=https://garage.learndatascience.cloud
```

### `load_task_bdd` — Ré-entraînement incrémental

Requête directement la vue `v_training_data` depuis PostgreSQL local,
puis applique le même prétraitement que `preprocess_training_data.py` en mémoire.

- **Config** : `config.yaml` avec profil `local` ou `neon`
- **Vue** : `v_training_data` (jointure enedis_conso × meteo × vacances)

---

## Lancement

### Entraînement initial (source S3)

```bash
uv run python src/jenedai/ml/scripts/train_flow.py --source s3
```

### Ré-entraînement depuis la BDD locale

```bash
uv run python src/jenedai/ml/scripts/train_flow.py --source bdd
```

### Déploiement avec scheduler (cron 19h00 quotidien)

```bash
uv run python src/jenedai/ml/scripts/train_flow.py --source bdd --deploy
```

> Le mode `--deploy` tourne en permanence et attend le cron.
> Sans `--deploy`, le flow s'exécute une seule fois et s'arrête.

---

## Étapes du pipeline

### 1. Validation — `validate_task`

Vérifie la qualité des données via `DataValidator` :
schéma, types, valeurs manquantes, cohérence métier.

### 2. Cast — `cast_task`

Force les types pandas attendus par le modèle via `DataCaster`.

### 3. Transformation — `transform_task`

Applique les features engineering via `Transformer` :
encodage, normalisation, création de variables temporelles.

### 4. Entraînement — `train`

Lance `EnergyPredictor` (RandomForest, `n_estimators=100`, `max_depth=10`)
et logue dans MLflow :

| Artefact    | Détail                                                  |
| ----------- | -------------------------------------------------------- |
| Modèle     | `pipeline_energy_predictor` (sklearn Pipeline complet) |
| Métriques  | `mae`, `r2`                                          |
| Paramètres | `n_estimators`, `max_depth`, `random_state`        |
| Alias       | `challenger` posé automatiquement après le run       |

### 5. Enregistrement — `register`

Promeut le modèle `challenger` en `champion` dans le MLflow Model Registry.

---

## MLflow

Le serveur MLflow doit être démarré avant le flow :

```bash
./start_MLflow.sh
```

Interface disponible sur `http://localhost:5000`en local ou sur l'URL fournie par HuggingFace.

Expérience cible : `energy_predictor`
Modèle enregistré : `pipeline_energy_predictor` (voir `constants.py` → `MODEL_NAME`)

---

---

## Prérequis

```bash
uv add prefect mlflow boto3 scikit-learn sqlalchemy psycopg2-binary pyyaml python-dotenv
```

PostgreSQL local démarré (pour la source `bdd`) :

```bash
docker compose up -d postgres
```

## Utile

Si des runs s'accumulent dans la queue `consume_energy_etl` et qu'on veut les annuler tous :

```bash
for state in SCHEDULED PENDING LATE; do
  prefect flow-run ls --state $state 2>/dev/null | awk '/consume_energy_etl/ {print $2}' | xargs -I {} prefect flow-run cancel {} 2>/dev/null
done
```

ou directement avec l'id :

```bash
# Voir tous les rus scheduled
prefect flow-run ls --state Scheduled
#cancel a specific run
prefect flow-run cancel 06a3814e-d0c1-7756-8000-5432187d4806
```
