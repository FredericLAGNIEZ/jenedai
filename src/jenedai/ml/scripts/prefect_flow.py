import os
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

# Imports légers
from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash


def _setup():
    """Initialisation unique au process principal."""
    from dotenv import load_dotenv

    load_dotenv(override=True)

    src_path = Path(__file__).parents[3]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    print("Python:", sys.executable)


# from sqlalchemy import create_engine
# import psycopg2
# from prefect.blocks.notifications import SlackWebhook  # optionnel
# from datetime import timedelta

# Local imports
# from prefect.settings import PREFECT_API_URL
# from prefect.runner.storage import GitRepository

# from importlib.metadata import vrsion
# try:
#     mlflow_version = mlflow.__version__
# except AttributeError:
#     mlflow_version = version("mlflow")
# print("mlflow version :", mlflow_version)


#############################################################################################
# TASK
#############################################################################################

## LOADING DATA


@task(
    name="load",
    retries=1,
    retry_delay_seconds=30,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(hours=1),
    tags=["load"],
)
def load_task(data_path: str) -> pd.DataFrame | None:
    from jenedai.ml.models.load_data_jenedai import load_data

    logger = get_run_logger()
    try:
        logger.info("Extracting data from source...")
        df = load_data(logger, data_path)
        logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns.")
        return df
    except Exception as e:
        msg = "Loading error on Data Pipeline"
        logger.error(f" {msg} : {e}")
        return None


@task(
    name="monitor",
    retries=1,
    retry_delay_seconds=30,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(hours=1),
    tags=["monitor"],
)
def monitor_task(data_path_reference: str, data_path: str) -> pd.DataFrame | None:
    import warnings

    from evidently import DataDefinition, Dataset, Report
    from evidently.presets import DataDriftPreset

    from jenedai.ml.models.load_data_jenedai import load_data

    # Ignore only RuntimeWarnings
    warnings.simplefilter("ignore", RuntimeWarning)

    logger = get_run_logger()

    try:
        logger.info("Extracting data from source...")
        reference = load_data(logger, data_path_reference)
        production = load_data(logger, data_path)

        # from evidently import ColumnMapping
        # Définir les colonnes à surveiller
        # column_mapping = ColumnMapping(
        #     target= 'total_energie_soutiree_wh',
        #     numerical_features=['nb_points_soutirage'],  # A ADAPTER
        #     categorical_features=['ville']
        # )

        parsed_reference = Dataset.from_pandas(reference, data_definition=DataDefinition())
        parsed_production = Dataset.from_pandas(production, data_definition=DataDefinition())

        report = Report([DataDriftPreset()])
        data_stability = report.run(current_data=parsed_production, reference_data=parsed_reference)
        data_drift_dict = data_stability.dict()

        logger.info(f"Sample : {data_drift_dict['metrics'][1]}")

    except Exception as e:
        msg = "Loading error on Monitor Data Pipeline"
        logger.error(f" {msg} : {e}")
        return None


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
def train(df):
    import mlflow
    from constants import MODEL_NAME, TRACKING_URI_HF

    from jenedai.ml.models.energy_predictor import EnergyPredictor

    # Ces 3 variables sont lues par boto3 sous-jacent à MLflow
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ.get("MLFLOW_S3_ENDPOINT_URL")
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")

    mlflow.set_tracking_uri(TRACKING_URI_HF)
    mlflow.set_experiment("energy_predictor")

    with mlflow.start_run() as run:
        print(f"Active run_id: {run.info.run_id}")
        predictor = EnergyPredictor(100, 10, 42)
        results = predictor.fit(df)

        mlflow.log_metrics({"mae": results["mae"], "r2": results["r2"]})
        mlflow.log_params({"n_estimators": 100, "max_depth": 10, "random_state": 42})
        mlflow.sklearn.log_model(
            predictor.model,
            name="random_forest",
            pip_requirements=["scikit-learn==1.8.0", "cloudpickle==3.1.2"],
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )
        model_uri = f"runs:/{run.info.run_id}/random_forest"
        mv = mlflow.register_model(model_uri, MODEL_NAME)

    return mv


# To add : Evidenttly AI : sarch for data drif...


@task(name="Register Model", retries=1, retry_delay_seconds=30, tags=["Register model"])
def register(mv):
    import mlflow
    from constants import MODEL_NAME

    client = mlflow.MlflowClient()
    client.transition_model_version_stage(
        name=MODEL_NAME,  # constante globale
        version=mv.version,
        stage="Production",
    )
    print(f"Modèle promu en Production (version {mv.version})")
    return mv.version


#############################################################################################
# FLOW
#############################################################################################


@flow(
    name="consume_energy_etl",
    description="ETL pipeline for energy consumption data.",
    log_prints=True,
    timeout_seconds=3600,  # 1h max
)
def etl():
    """
    Main Pipeline entry
    """
    from jenedai.ml.utils.get_console import get_console
    from jenedai.ml.utils.logs import configure_logging

    data_folder = Path("./data")
    logs_folder = Path(__file__).parents[3] / "logs"
    print(f"CWD: {os.getcwd()}")
    print(f"__file__: {__file__}")

    data_path = data_folder / "extract_cvs_engis_dataset.csv"
    print(f"data_path: {data_path}")
    data_path_reference = data_folder / "extract_cvs_engis_dataset_reference.csv"
    print(f" data_path_reference: {data_path_reference}")

    if data_path.exists():
        print(f"data_path exists: {data_path.exists()}")
        print(f"CSV size: {os.path.getsize(data_path) if data_path.exists() else 'NOT FOUND'}")
    else:
        print(f"Contenu du dossier data: {list(Path(os.getcwd()).glob('data/*'))}")

    # Hors système de logging
    console = get_console()

    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]🔍 ML Enedis Pipeline[/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]\n")

    # ✅ Système de logging
    logger = configure_logging(
        path_logs=logs_folder,
        name="ML Enedis",
        profile="basic",
    )
    logger.info("Système de logs configuré")

    # Data_pipeline : loading
    try:
        console.print(f"Data_path : {data_path}")
        df = load_task(str(data_path))
        if df is None:
            raise ValueError("load_task n'a retourné aucune donnée.")
        if df.empty:
            raise ValueError("Le DataFrame chargé est vide.")
        else:
            console.print("✓ Data loaded\n")
    except Exception as e:
        msg = "Data Loading Pipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : Monitoring
    try:
        monitor_task(str(data_path_reference), str(data_path))
        console.print("✓ Data Monitored \n")
    except Exception as e:
        msg = "Data Loading Pipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : validation
    try:
        console.print("Validation des données...")
        df = validate_task(df)
        if df is None:
            raise ValueError("Validation task n'a retourné aucune donnée.")
        if df.empty:
            raise ValueError("Le DataFrame validé est vide.")
        console.print("✓ Data Validated\n")
        console.print(f"✓ DataFrame has now {df.shape[0]} lines\n")
    except Exception as e:
        msg = "Data Validation Pipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : cast
    try:
        console.print("Cast données...")
        df = cast_task(df)
        if df is None:
            raise ValueError("Cast task n'a retourné aucune donnée.")
        if df.empty:
            raise ValueError("Le DataFrame casted est vide.")
        console.print("✓ Data Casted\n")
        console.print(f"✓ DataFrame has now {df.shape[0]} lines\n")
    except Exception as e:
        msg = "Data Cast Pipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : transformation
    try:
        console.print("Transformation des données...")
        df = transform_task(df)
        if df is None:
            raise ValueError("transform_task n'a retourné aucune donnée.")
        if df.empty:
            raise ValueError("Le DataFrame transformé est vide.")
        console.print("✓ Data Transformed\n")
        console.print(f"✓ DataFrame has now {df.shape[0]} lines\n")
    except Exception as e:
        msg = "Data Transformation Pipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : ML Training (MLflow)
    try:
        console.print("Entrainement du modèle...")
        mv = train(df)
        if mv is None:
            raise ValueError("train task n'a retourné aucun modèle.")
        else:
            console.print("✓ Model trained\n")
    except Exception as e:
        msg = "Model TrainingPipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise

    # Data_pipeline : Model Register (MLflow)
    try:
        console.print("Enregistrement du modèle dans le registry...")
        register(mv)
    except Exception as e:
        msg = "Model Register Pipeline Error "
        logger.error(f" ❌ {msg} : {e}")
        raise


if __name__ == "__main__":
    _setup()
    try:
        # etl()
        #  Démarre un scheduler local, attends que le cron se déclenche
        #  Se connecte à Prefect (local ou cloud)
        #  Il enregistre le déploiement auprès du serveur Prefect (API) pour qu'il soit visible dans l'UI.
        # 3 — Spawn un subprocess à chaque run
        # Quand le cron se déclenche, il lance un nouveau process Python qui ré-importe ton fichier et exécute etl().
        etl.serve(
            name="consume-energy",
            cron="*/10 * * * *",  # tous les jours à 6h UTC
            tags=["energy", "etl"],
            description="Daily energy consumption ETL and ML.",
            pause_on_shutdown=False,
            limit=1,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")

        # Deploiement directement dans le script python
        #  if __name__ == "__main__":
        #     try:
        #         etl.deploy(
        #             name="consume-energy",
        #             work_pool_name="energy-pool"
        #             cron="*/5 * * * *",
        #             tags=["energy", "etl"],
        #             description="Daily energy consumption ETL and ML.",
        #             source=GitRepository(
        #                 url="https://github.com/Jenedai/jenedai",
        #                 branch="mlops_frederic",
        #             ))
        #     except KeyboardInterrupt:
        #         print("\n\n⚠️  Interruption utilisateur")
        #     except Exception as e:
        #         print(f"\n❌ Erreur fatale: {e}")


# Erreur dans mlflow :Failed to list artifacts in s3://mlflow-artifacts/4/9ff72effe59845d09acf187607b5f755/artifacts:
#  Forbidden: No such key: a652ae928559f7425f33a94d79eff033
