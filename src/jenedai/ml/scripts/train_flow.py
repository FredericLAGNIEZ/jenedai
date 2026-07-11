import os
import sys
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd

# Imports légers
from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash

from jenedai.ml.models.evidently_monitoring import monitor_task


# ── Setup ─────────────────────────────────────────
def _setup():
    """Initialisation unique au process principal."""
    from dotenv import load_dotenv

    # Chargement environnement
    load_dotenv(override=True)

    src_path = Path(__file__).parents[3]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    print("Python:", sys.executable)


# Chargement par défaut
_setup()

# ── Config ─────────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).parents[3] / "jenedai" / "data" / "connectors"
CONFIG_PATH = SCRIPTS_DIR / "config.yaml"
PROFILE = "local"

#############################################################################################
# TASK
#############################################################################################

## LOADING TRAINING DATA


@task(name="load_s3", retries=1, retry_delay_seconds=30, tags=["load", "s3"])
def load_task_s3(logger_file: str, data_folder: str) -> pd.DataFrame | None:
    import boto3

    from jenedai.ml.models.load_data_jenedai import load_data_csv

    logger = get_run_logger()

    # Load CSV file from Garage S3
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url="https://garage.learndatascience.cloud",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name="garage",
        )

        logger.info("S3 Client established successfully")
        logger_file.info("S3 Client established successfully")
    except Exception as e:
        msg = "Loading error on establishing S3 Client."
        logger_file.error(f" {msg} : {e}")
        logger.error(f" {msg} : {e}")
        return None

    # Download the file from S3 to local path
    file_key = "dataset_train.csv"
    bucket_name = "jenedai"
    local_path = Path(data_folder) / "dataset_train.csv"

    try:
        s3.download_file(bucket_name, file_key, local_path)
        msg = "Fichier S3 téléchargé avec succès"
        logger.info(msg)
        logger_file.info(msg)
    except Exception as e:
        msg = "Loading error on S3 Downloading file."
        logger_file.error(f" {msg} : {e}")
        logger.error(f" {msg} : {e}")
        return None

    # Load data from CSV file
    try:
        logger.info("Extracting dataset_train.CSV file for initial training...")
        df = load_data_csv(logger, local_path)
        msg = f"Extracted {len(df)} rows, {len(df.columns)} columns."
        logger_file.info(msg)
        logger.info(msg)
        return df
    except Exception as e:
        msg = "Loading error on Extracting dataset_train.CSV file for initial training."
        logger.error(f" {msg} : {e}")
        return None


@task(
    name="load_bdd",
    retries=1,
    retry_delay_seconds=30,
    tags=["load", "bdd"],
)
def load_task_bdd(config_path: str, profile: str = "local") -> pd.DataFrame | None:
    """
    Requête v_training_data depuis PostgreSQL local et prétraite en mémoire.
    Réutilise la logique de preprocess_training_data.py sans passer par un CSV.
    """
    import sqlalchemy
    import yaml

    from jenedai.ml.models.preprocess_training_data import (
        normalize_booleans,
        normalize_categoricals,
        normalize_dates,
        normalize_datetimes,
        normalize_numerics,
        report,
    )

    logger = get_run_logger()

    # ── Connexion ──────────────────────────────────────────────────────────────
    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        db_cfg = cfg["database"]
        db = db_cfg[profile] if profile in db_cfg else db_cfg

        pwd = db.get("password") or ""
        auth = f"{db['user']}:{pwd}@" if pwd else f"{db['user']}@"
        sslmode = db.get("sslmode", "disable")
        url = (
            f"postgresql+psycopg2://{auth}{db['host']}:{db['port']}/{db['name']}?sslmode={sslmode}"
        )

        engine = sqlalchemy.create_engine(url, pool_pre_ping=True)
        logger.info(f"Connexion OK → {db['host']}:{db['port']}/{db['name']} (profil: {profile})")
    except Exception as e:
        logger.error(f"Erreur connexion BDD : {e}")
        return None

    # ── Requête ────────────────────────────────────────────────────────────────
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(
                sqlalchemy.text("SELECT * FROM v_training_data"),
                conn,
            )
        logger.info(f"v_training_data : {len(df):,} lignes × {len(df.columns)} colonnes")
    except Exception as e:
        logger.error(f"Erreur requête v_training_data : {e}")
        return None

    if df.empty:
        logger.warning("v_training_data est vide — aucune donnée retournée.")
        return None

    # ── Prétraitement (même pipeline que preprocess_training_data.py) ──────────
    try:
        df = normalize_booleans(df)
        df = normalize_datetimes(df)
        df = normalize_dates(df)
        df = normalize_numerics(df)
        df = normalize_categoricals(df)
        report(df)
        logger.info(f"Prétraitement OK — {len(df):,} lignes prêtes pour l'entraînement")
    except Exception as e:
        logger.error(f"Erreur prétraitement : {e}")
        return None

    return df


## MONITORING DATA VOIR IMPORTS


## VALIDATING DATA
@task(
    name="validate",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["validation"],
)
def validate_task(df: pd.DataFrame) -> pd.DataFrame | None:
    from jenedai.ml.models.data_validator_jenedai import DataValidator

    logger = get_run_logger()
    try:
        logger.info(f"Running data quality checks on {len(df)} rows...")
        datavalidator = DataValidator()
        validated_df = datavalidator.validate(df)
        logger.info("Validation passed.")
        return validated_df
    except Exception as e:
        msg = "Validation error on Data Pipeline"
        logger.error(f" {msg} : {e}")
        return None


## CASTING DATA TYPES
@task(
    name="cast",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["cast"],
)
def cast_task(df: pd.DataFrame) -> pd.DataFrame | None:
    from jenedai.ml.models.data_caster_jenedai import DataCaster

    logger = get_run_logger()
    try:
        logger.info("Running cast types on df...")
        datacaster = DataCaster()
        casted_df = datacaster.cast(df)
        logger.info("Cast done.")
        return casted_df
    except Exception as e:
        msg = "Validation error on Cast Pipeline"
        logger.error(f" {msg} : {e}")
        return None


## TRANSFORMING DATA
@task(
    name="transform",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["transformation"],
)
def transform_task(df: pd.DataFrame) -> pd.DataFrame | None:
    from jenedai.ml.models.data_transformer_jenedai import Transformer

    logger = get_run_logger()
    try:
        logger.info("Applying transformations...")
        transformer = Transformer()
        transformed_df = transformer.transform(df)
        logger.info(f"Transformation complete. Output shape: {transformed_df.shape}")
        return transformed_df
    except Exception as e:
        msg = "Validation error on Tranform Pipeline"
        logger.error(f" {msg} : {e}")
        return None


@task(name="Train Model", retries=1, retry_delay_seconds=30, tags=["Training model"])
def train(df, logger_file):
    import mlflow
    from constants import MODEL_NAME, TRACKING_URI
    from mlflow.models.signature import infer_signature

    from jenedai.ml.models.energy_predictor import EnergyPredictor

    logger = get_run_logger()

    # Ces 3 variables sont lues par boto3 sous-jacent à MLflow
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ.get("MLFLOW_S3_ENDPOINT_URL")
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")

    # Charger le pipeline complet (préprocessor + modèle)
    mlflow.set_tracking_uri(TRACKING_URI)
    ### MLFLOW Experiment setup
    experiment_name = "energy_predictor"
    # mlflow.delete_experiment(mlflow.get_experiment_by_name(experiment_name).experiment_id)
    mlflow.set_experiment(experiment_name)  # recrée avec le bon artifact root

    # client = mlflow.tracking.MlflowClient()
    # run = client.create_run(experiment.experiment_id) # utile??
    logger_file.info("LAUNCHING TRAIN FLOW")

    # Time execution
    start_time = time.time()

    with mlflow.start_run() as run:
        msg = f"Active run_id: {run.info.run_id}"
        logger.info(msg)
        logger_file.info(msg)
        predictor = EnergyPredictor(100, 10, 42)
        X_train, Y_pred, results = predictor.fit(df)

        sample_input = X_train.head(5)
        # sample_output = predictor.predict(sample_input)
        # signature = infer_signature(sample_input, sample_output)

        # pipeline = Pipeline([
        #     ('preprocessor', predictor.preprocessor),
        #     ('model', predictor.model)
        # ])
        # sample_output = pipeline.predict(sample_input)

        # ✅ Utiliser directement le pipeline déjà fitté
        sample_output = predictor.pipeline.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)

        signature = infer_signature(sample_input, sample_output)
        registered_model_name = "pipeline_energy_predictor"
        # Créer un pipeline complet (préprocessor + modèle)
        # Sauvegarder le pipeline complet
        mlflow.sklearn.log_model(
            predictor.pipeline,
            name=registered_model_name,
            signature=signature,
            input_example=sample_input,
            pip_requirements=["scikit-learn==1.8.0", "cloudpickle==3.1.2"],
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )

        # Enregistrer le pipeline comme modèle
        pipeline_uri = f"runs:/{run.info.run_id}/{registered_model_name}"
        mv = mlflow.register_model(pipeline_uri, MODEL_NAME)

        # Sauvegarder les métriques
        mlflow.log_metrics({"mae": results["mae"], "r2": results["r2"]})
        mlflow.log_params({"n_estimators": 100, "max_depth": 10, "random_state": 42})

    logger.info("...Done!")
    logger.info(f"---Total training time: {time.time() - start_time}")

    # Poser l'alias "challenger" sur la version enregistrée
    client = mlflow.tracking.MlflowClient()
    client.set_registered_model_alias(
        name=MODEL_NAME,
        alias="challenger",
        version=mv.version,
    )
    logger.info(f"[INFO] Alias 'challenger' → version {mv.version}")

    return mv


@task(name="Register Model", retries=1, retry_delay_seconds=30, tags=["Register model"])
def register(mv):
    import mlflow
    from constants import MODEL_NAME

    client = mlflow.MlflowClient()

    client.set_registered_model_alias(
        name=MODEL_NAME,
        alias="champion",
        version=mv.version,
    )
    print(f"[INFO] Alias 'champion' → version {mv.version}")
    return mv.version


#############################################################################################
# FLOW
#############################################################################################


@flow(
    name="consume_energy_etl_jenedai",
    description="ETL pipeline for energy consumption data.",
    log_prints=True,
    timeout_seconds=3600,  # 1h max
)
def etl(source: str = "s3"):
    """
    Main Pipeline entry
    """
    from jenedai.ml.utils.get_console import get_console
    from jenedai.ml.utils.logs import configure_logging

    data_folder = Path("./data")
    logs_folder = Path(__file__).parents[4] / "logs"
    # print(f"CWD: {os.getcwd()}")
    # print(f"__file__: {__file__}")

    if data_folder.exists():
        print(f"data_folder exists: {data_folder}")
        print(f"Contenu: {list(data_folder.iterdir())}")

    # Hors système de logging
    console = get_console()

    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]🔍 Energy predictor Enedis Pipeline[/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]\n")

    # ✅ Système de logging
    logger_file = configure_logging(
        path_logs=logs_folder,
        name="ML_enedis",
        profile="basic",
    )
    logger_file.info("Système de logs configuré")

    # Data_pipeline : loading
    try:
        if source == "s3":
            console.print(f"Data_folder : {data_folder}")
            df = load_task_s3(logger_file, data_folder)
            if df is None:
                msg = "Load_task n'a retourné aucune donnée."
                console.print(msg)
                logger_file.info(msg)
                raise ValueError(msg)
            if df.empty:
                msg = "Le DataFrame chargé est vide."
                console.print(msg)
                logger_file.info(msg)
                raise ValueError(msg)
            else:
                msg = "✓ Data loaded\n"
                console.print(msg)
                logger_file.info(msg)

        elif source == "bdd":
            df = load_task_bdd(config_path=str(CONFIG_PATH), profile=PROFILE)
            # Validation des données avec EVIDENTLY AI
            df_reference = load_task_s3(logger_file, data_folder)

            NUMERIC_COLS = [
                "total_energie_soutiree_wh",
                "nb_points_soutirage",
                "lat",
                "lon",
                "temperature_2m_mean",
                "relative_humidity_mean",
                "precipitation_sum",
            ]

            for col in NUMERIC_COLS:
                if col in df_reference.columns:
                    df_reference[col] = pd.to_numeric(df_reference[col], errors="coerce")
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    # logger_file.info(f"{col} (production) dtype après cast: {df[col].dtype}")

            _data_drift_dict = monitor_task(df_reference, df)

            msg = " Data Drift evaluated\n"
            console.print(msg)
            logger_file.info(msg)

        else:
            df = None

    except Exception as e:
        msg = "Data Loading Pipeline Error "
        logger_file.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : validation
    try:
        console.print("Validation des données...")
        df = validate_task(df)
        if df is None:
            msg = "Validation task n'a retourné aucune donnée."
            console.print(msg)
            logger_file.info(msg)
            raise ValueError(msg)
        if df.empty:
            msg = "Le DataFrame validé est vide."
            console.print(msg)
            logger_file.info(msg)
            raise ValueError(msg)
        msg = "✓ Data Validated\n ✓ DataFrame has now {df.shape[0]} lines\n"
        console.print(msg)
        logger_file.info(msg)
    except Exception as e:
        msg = "Data Validation Pipeline Error "
        logger_file.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : cast
    try:
        console.print("Cast données...")
        df = cast_task(df)
        if df is None:
            msg = "Cast task n'a retourné aucune donnée."
            console.print(msg)
            logger_file.info(msg)
            raise ValueError(msg)
        if df.empty:
            msg = "Le DataFrame casted est vide."
            console.print(msg)
            logger_file.info(msg)
            raise ValueError(msg)
        msg = f"✓ Data Casted\n ✓ DataFrame has now {df.shape[0]} lines\n"
        console.print(msg)
        logger_file.info(msg)
    except Exception as e:
        msg = "Data Cast Pipeline Error "
        logger_file.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : transformation
    try:
        console.print("Transformation des données...")
        df = transform_task(df)
        if df is None:
            msg = "Transform_task n'a retourné aucune donnée."
            console.print(msg)
            logger_file.info(msg)
            raise ValueError(msg)
        if df.empty:
            msg = "Le DataFrame transformé est vide."
            console.print(msg)
            logger_file.info(msg)
            raise ValueError(msg)

        msg = f"✓ Data Transformed\n DataFrame has now {df.shape[0]} lines\n"
        console.print(msg)
        logger_file.info(msg)
    except Exception as e:
        msg = "Data Transformation Pipeline Error "
        logger_file.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : ML Training (MLflow)
    try:
        console.print("Entrainement du modèle...")
        mv = train(df, logger_file=logger_file)
        if mv is None:
            raise ValueError("train task n'a retourné aucun modèle.")
        else:
            console.print("✓ Model trained\n")
    except Exception as e:
        msg = f"Model Training Pipeline Error : {e}"
        console.print(msg)
        logger_file.info(msg)
        raise

    # Data_pipeline : Model Register (MLflow)
    try:
        msg = "Enregistrement du modèle dans le registry..."
        console.print(msg)
        logger_file.info(msg)
        register(mv)
    except Exception as e:
        msg = f"Model Register Pipeline Error : {e}"
        console.print(msg)
        logger_file.info(msg)
        raise


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default=None, choices=["s3", "bdd"])
    parser.add_argument("--deploy", action="store_true", help="Lancer le scheduler cron")
    args = parser.parse_args()
    source = args.source if args.source else os.getenv("SOURCE", "s3")

    if args.deploy:
        # Mode scheduler — tourne en permanence, attend le cron
        try:
            #  Démarre un scheduler local, attends que le cron se déclenche.
            # Le scheduler est un processus Python qui tourne en permanence.
            # Il attend que le cron se déclenche
            # Il se connecte à Prefect (local ou cloud). Il enregistre le déploiement auprès 
            # u serveur Prefect (API) pour qu'il soit visible dans l'UI.
            # 3 — Spawn un subprocess à chaque run
            # Quand le cron se déclenche, il lance un nouveau process Python qui ré-importe
            # ton fichier            # et exécute etl().
            # Appel du flow avec le paramètre source
            etl.serve(
                name="consume-energy",
                cron="59 7 * * *",
                tags=["energy", "etl"],
                description="Daily energy consumption ETL and ML.",
                pause_on_shutdown=False,
                limit=1,
                parameters={"source": source},
            )
        except KeyboardInterrupt:
            print("\n\n⚠️ Interruption utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
    else:
        # Mode test — run unique, s'arrête tout seul
        etl(source=source)
