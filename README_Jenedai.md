# Déploiement Prefect — Jenedai

Prefect orchestre l'exécution du pipeline ML, localement ou sur le cloud, selon un planning ou à la demande.

---

## Comment ça fonctionne

```mermaid
flowchart TD
    A[Code Python\nFlow Prefect] --> B{Déploiement}
    B -->|Cloud| C[Prefect Cloud\nUI + scheduling]
    B -->|Local| D[serve local\ntest_prefect.py]
    C --> E[Work Pool\nenergy-pool]
    E --> F[Worker managé\nPrefect Cloud]
    F --> G[Exécution\ndu Flow]
    D --> G
    G --> H[MLflow Tracking\njenedai-mlflow.hf.space]
    G --> I[Artefacts S3\nmlflow-artifacts]
```

---

## Cycle de vie d'un run

```mermaid
stateDiagram-v2
    [*] --> Scheduled : prefect deployment run
    Scheduled --> Pending : worker disponible
    Pending --> Running : exécution démarrée
    Running --> Completed : succès
    Running --> Failed : erreur
    Failed --> Scheduled : retry automatique
    Completed --> [*]
```

---


## Déploiement Cloud (Prefect Managed)

### 1. Prérequis

- Se connecter avec le compte **Jenedai** sur Prefect Cloud et GitHub.
- Installer uv pour plus de facilité

### 2. Activer l'environnement
model_uri 
```bash
source .venv/bin/activate
```

### 3. Se logger sur Prefect

```bash
prefect cloud login
```

or

```bash
uv run python -m prefect cloud login
```


### 4. Vérifier / créer le work pool

Un Work pool in Prefect est la file d'attente où vos « workers » viennent chercher les flows à exécuter.

```bash
# Lister les pools existants
prefect work-pool ls

# Si energy-pool n'existe pas, créer un workpool en mode « managed » (hébergée et gérée par Prefect Cloud ; vous n'avez pas besoin de gérer vous-même les machines).
prefect work-pool create energy-pool --type prefect:managed
```

or

```bash
uv run python -m prefect work-pool ls
```

> Un **work pool** de type `prefect:managed` délègue l'exécution à l'infrastructure Prefect Cloud — pas besoin de worker local.

### 5. Déployer depuis GitHub

```bash
prefect deploy -n consume-energy
```

Cette commande publie (déploie) un flux sur Prefect Cloud/Server pour qu'il soit prêt à être exécuté. Cela lit le re fichier de configuration prefect.yaml et enregistre le déploiement auprès de l'API Prefect.

-n consume-energy : Cible un seul déploiement par son nom — celui défini dans votre config sous l'entrée consume-energy.

Le flux est lancé automatiquement dans l'UI en fonciton du  fichier yaml.

### 6. Observer les runs sur l'UI

Interface : [app.prefect.io](https://app.prefect.io)
Le lien de l'UI est donné lors du déploiement.

> ⚠️ La limite est 500 minutes CPU par cycle de facturation sur le plan gratuit; donc est très limitée.
Pour le dév, on va préférer le déploiement en local.

---

## Déploiement local

Utile pour tester sans consommer de crédits cloud.

```mermaid
sequenceDiagram
    participant Dev
    participant Prefect API
    participant Flow

    Dev->>Flow: uv run python src/jenedai/ml/scripts/prefect_flow.py  # Flow is being served with 
    Flow->>Prefect API: serve(name="consume-energy")
    Dev->>Prefect API: prefect deployment run 'consume_energy_etl/consume-energy' # schedule a run # etl.serve(name="cpd-pipeline-deployment", cron="0 0 * * *")
    Prefect API->>Flow: déclenche le run
    Flow-->>Dev: logs en temps réel
```

or

```bash
.venv/bin/python3 src/jenedai/ml/scripts/prefect_flow.py
```

### Planifier avec un cron (dans le code prefect_flow.py)

```python
etl.serve(
    name="consume-energy",
    cron="0 0 * * *"   # tous les jours à minuit
)
```

---

## Commandes utiles

| Action | Commande |
|---|---|
| Inspecter un déploiement | `prefect deployment inspect consume_energy_etl/consume-energy` |
| Lister les runs | `prefect flow-run ls` |
| Supprimer un déploiement | `prefect deployment delete consume_energy_etl/consume-energy` |
| Voir les work pools | `prefect work-pool ls` |
| Voir les workers actifs | `prefect worker ls` |

---

## Ressources

- [Prefect Cloud](https://app.prefect.io)
- [Documentation Prefect](https://docs.prefect.io)
- [MLflow Tracking](https://jenedai-mlflow.hf.space)

# MLFlow

## MLflow Model Registry

Le Model Registry est le catalogue central de tous vos modèles. Il gère les versions, les stages, et fait le lien entre l'entraînement et la production.

Un model registry, c'est le catalogue central de tous tes modèles entraînés.Un model registry, c'est le catalogue central de tous tes modèles entraînés. Il joue trois rôles clés :
Stocker et versionner — chaque modèle entraîné est sauvegardé avec ses métadonnées : métriques de performance, hyperparamètres, dataset utilisé, date d'entraînement. Tu peux comparer deux versions et savoir exactement ce qui a changé.
Gérer le cycle de vie — un modèle passe par des états : Staging (en test) → Production (déployé) → Archived (retiré). Le registry garde la trace de ces transitions et qui les a approuvées.
Servir de pont avec le déploiement — le pipeline CI/CD va chercher le modèle "Production" dans le registry pour le déployer. Ça découple l'entraînement du déploiement : tu n'as pas besoin de redéployer ton infra pour changer de modèle, tu changes juste le tag dans le registry.

---

### Architecture

```mermaid
flowchart LR
    A[Entraînement\nlocal] -->|log_model| B[MLflow Tracking URI\njenedai-mlflow.hf.space]
    B -->|register_model| C[Model Registry]
    B -->|artefacts| D[(S3 sur SupaBase\nMLflow-artifacts)]
    C -->|load_model| E[Production API]
```

**Tracking URI :** `https://jenedai-mlflow.hf.space`
**Artifact store :** `s3://mlflow-artifacts`

---

### Cycle de vie d'un modèle

```mermaid
stateDiagram-v2
    [*] --> None : register_model()
    None --> Staging : transition_stage()
    Staging --> Production : transition_stage()
    Staging --> None : rejet
    Production --> Archived : nouveau modèle
    Archived --> [*]
```

---

### Mlflow en local

## Create a local db or usr defautl sqlite db

sudo -u postgres createuser --superuser frederic
sudo -u postgres psql -c "CREATE DATABASE mlflow OWNER frederic;"
psql -d mlflow "ALTER USER frederic PASSWORD 'frederic'



## Start **Local** MLflow tracking server

This CMD in a bash file allows you to start a local MLflow server.

```bash
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlruns \
  --host 0.0.0.0 \
  --port 5000 \
  --gunicorn-opts "--timeout 180"
```

or

Create a local db

```bash
sudo -u postgres createuser --superuser frederic
sudo -u postgres psql -c "CREATE DATABASE mlflow OWNER frederic;"
sudo -u postgres psql -c "ALTER USER frederic PASSWORD 'frederic';"
```

This CMD in a bash file allows you to start a local MLflow server.

```bash
mlflow server \
  --backend-store-uri postgresql://frederic:frederic@localhost:5432/mlflow \
  --default-artifact-root s3://jenedai/ \
  --host 0.0.0.0 \
  --port 5000
  --gunicorn-opts "--timeout 180"
```

### Create a script

Launch local MLflow server

```bash
chmod +x start_mlflow.sh
./start_mlflow.sh
```

> **Note:** The MLflow Model Registry requires metadata to be stored in a SQL database (`--backend-store-uri`). A flat file store will not work.

### Parameter reference

| Parameter | Description |
|---|---|
| `--backend-store-uri` | Location and type of database used to store high level metadata associated with our runs (metrics, params, tags). Here, a local SQLite file. |
| `--default-artifact-root` | Path where artifacts (models, plots, files) are stored. A separate path is provided for artifacts because artifacts can be very large and therefore may need to be stored in a cloud-based data store such as S3 for some projects. Use a cloud path (e.g. `s3://my-bucket/mlruns`) for large or shared projects. |
| `--host 0.0.0.0` | Binds the server to all network interfaces, making it reachable beyond localhost. |
| `--port 5000` | Port the server listens on. |
| `--gunicorn-opts "--timeout 180"` | Extends the worker timeout to 180 s — useful for slow artifact uploads. |

---

## Set the Tracking URI in your code

```python
mlflow.set_tracking_uri("http://127.0.0.1:5000")
```

A very important step to tell MLflow where the model tracking server is.

Call this before any `mlflow.log_*` or `mlflow.start_run()` call. It tells the MLflow client where to send tracking data.

---

## Access the MLflow UI

Open your browser at:

**Tracking URI :** `http://127.0.0.1:5000`


Select your experience name.
Only the **Default** experiment will be listed on first launch.

---

## Cloud MLflow Tracking Server

### Start the server on Hugging Face with Dockerfile

This CMD in Dockerfile allows you to start an MLflow server on HF space.

```bash
CMD mlflow server --host 0.0.0.0 \
  --port 7860 \
  --backend-store-uri $MLFLOW_POSTGRES_URI \
  --default-artifact-root "s3://mlflow-artifacts/" \
  --allowed-hosts "*" \
  --cors-allowed-origins "*"
```

Penser à réactiver le space MLFLOW sur Hugging Face

---

### Set the Tracking URI in your code

```python
mlflow.set_tracking_uri("https://jenedai-mlflow.hf.space'") # URL du serveur MLflow
```


### Access the MLflow UI

Access the MLflow UI a this url, select your experience name.

---

# Save model on MLflow Model Registry

Mlflow registry is on PostgreSQL, either on SUPABSE if that works or in local : 








"## Inital training

Lauch db and mlflow
Activer environnement

./start_MLflow.sh









# Nom artefact

model_uri = f"runs:/{run_jenedai.info.run_id}/random_forest"
mv = mlflow.register_model(model_uri, MODEL_NAME)

client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name=MODEL_NAME,
    version=mv.version,
    stage="Production"
)
```

PB de l'accès de mlflow au S3 de supabase

Architectures possibles :
chitecture 1 — MLflow accède à S3 (actuelle)
Client Python → MLflow Server → S3 Supabase
                     ↑
              doit avoir les credentials
Le serveur MLflow gère tout — upload et listing des artifacts.

Architecture 2 — Client accède à S3 directement
Client Python → S3 Supabase  (artifacts)
Client Python → MLflow Server (métadonnées uniquement)
Configuré avec --serve-artifacts désactivé et en passant l'URI S3 directement depuis le client :
pythonimport mlflow
import os

# Le CLIENT a les credentials, pas le serveur
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "https://<REF>.supabase.co/storage/v1/s3"
os.environ["AWS_ACCESS_KEY_ID"] = "..."
os.environ["AWS_SECRET_ACCESS_KEY"] = "..."

mlflow.set_tracking_uri(TRACKING_URI_HF)

with mlflow.start_run():
    mlflow.sklearn.log_model(...)  # upload direct vers S3, bypass serveur
Et le serveur MLflow sans credentials S3 :
dockerfileCMD mlflow server --host 0.0.0.0 \
  --port 7860 \
  --backend-store-uri $MLFLOW_POSTGRES_URI \
  --default-artifact-root "s3://mlflow-artifacts/" \
  --no-serve-artifacts \        # ← le serveur ne proxifie pas S3
  --allowed-hosts "*" \


  # Actuellement 
  Artifact UR : Chemin HTTP genre mlflow-artifacts/... proxifié → le serveur gère les artifacts
---

### Load Model in production (TODO)

Once model saved in the registry :

```python
import mlflow.pyfunc

model = mlflow.pyfunc.load_model("models:/random_forest_model/Production")
predictions = model.predict(df)
```

---

my_clf = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/{version}")
MLflow fait deux choses :
1. Interroge PostgreSQL pour récupérer les métadonnées de la version 10 → obtient le run_id et l'URI S3 du modèle
2. Télécharge depuis S3 le fichier pickle du modèle

Donc si ça fonctionne...
✅ PostgreSQL accessible
✅ S3 Supabase accessible depuis votre machine locale
✅ Credentials S3 corrects côté client

Ce que ça confirme pour votre problème
Le problème de Forbidden sur list_artifacts vient uniquement du serveur MLflow sur HF Spaces qui n'a pas accès à S3 — pas de votre client Python qui lui fonctionne parfaitement.
La solution est donc soit :

Fixer les credentials S3 sur HF Spaces
Ou passer en architecture --no-serve-artifacts (le serveur n'a plus besoin de S3)



AWS_ENDPOINT_URL        → lue par boto3 / AWS CLI (standard AWS SDK)
MLFLOW_S3_ENDPOINT_URL  → lue par MLflow spécifiquement


# TODO: Evidently AI, PREDICTION


Appel direct au binaire qui fonctionnte : .venv/bin/python -m prefect deployment run 'consume_energy_etl/consume-energy'
