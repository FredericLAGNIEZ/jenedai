import os
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash

from jenedai.ml.models.data_caster_jenedai import DataCaster
from jenedai.ml.models.data_transformer_jenedai import Transformer
from jenedai.ml.models.data_validator_jenedai import DataValidator
from jenedai.ml.models.load_data_jenedai import load_data
from jenedai.ml.utils.get_console import get_console
from jenedai.ml.utils.logs import configure_logging

# src/jenedai/ml/scripts/test_prefect.py → remonte 3 niveaux → src/
src_path = Path(__file__).parents[3]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

load_dotenv()


@task(
    name="load",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["load"],
)
def load_task(data_path: str) -> pd.DataFrame | None:
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
    name="validate",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["validation"],
)
def validate_task(df: pd.DataFrame) -> pd.DataFrame | None:
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


@task(
    name="cast",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["cast"],
)
def cast_task(df: pd.DataFrame) -> pd.DataFrame | None:
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


@task(
    name="transform",
    retries=1,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["transformation"],
)
def transform_task(df: pd.DataFrame) -> pd.DataFrame | None:
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


@flow(
    name="consume_energy_etl",
    description="ETL pipeline for energy consumption data.",
    log_prints=True,
    timeout_seconds=3600,  # 1h max — évite les runs bloqués
)
def etl():
    """
    Point d'entrée principal des pipelines
    """
    # ✅ Chemins définis en premier dans le flow
    data_folder = Path("./data")
    # data_folder = Path(__file__).parents[3] / "data"  # ✅ absolu
    data_path = data_folder / "extract_cvs_engis_dataset.csv"

    logs_folder = Path(__file__).parents[3] / "logs"

    print(f"data_path: {data_path}")
    print(f"exists: {data_path.exists()}")

    print("Python:", sys.executable)
    print("sys.path:", sys.path)
    print("cwd:", sys.path)
    print("PYTHONPATH:", os.environ.get("PYTHONPATH", "NOT SET"))

    print(f"CWD: {os.getcwd()}")
    print(f"__file__: {__file__}")
    print(f"data_path exists: {data_path.exists()}")
    print(f"Contenu du dossier data: {list(Path(os.getcwd()).glob('data/*'))}")

    print(f"CSV exists: {data_path.exists()}")
    print(f"CSV size: {os.path.getsize(data_path) if data_path.exists() else 'NOT FOUND'}")

    # Hors système de logging
    console = get_console()

    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]🔍 ML Enedis [/bold cyan]")
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
        console.print(f"New new data_path : {data_path}")
        df = load_task(str(data_path))
        # ✅ Version défensive complète
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


# def create_postgres_table():
#     '''
#     Create the cpd_incidents table in Postgres DB (cpd_db) if it doesn't exist.
#     '''
#     # establish connection to DB
#     conn = psycopg2.connect(
#         host="localhost",
#         port="5433",
#         database="cpd_db",
#         user=os.getenv("POSTGRES_USER"),
#         password=os.getenv("POSTGRES_PASSWORD")
#     )

#     # create cursor object to execute SQL
#     cur = conn.cursor()

#     # execute query to create the table
#     create_table_query = '''
#         CREATE TABLE IF NOT EXISTS cpd_incidents (
#             date_time TIMESTAMP,
#             id INTEGER PRIMARY KEY,
#             type TEXT,
#             subtype TEXT,
#             location TEXT,
#             description TEXT,
#             last_updated TIMESTAMP,
#             year INTEGER,
#             month INTEGER,
#             day INTEGER,
#             hour INTEGER,
#             minute INTEGER,
#             second INTEGER
#         )
#     '''
#     cur.execute(create_table_query)

#     # commit changes
#     conn.commit()

#     # close cursor and connection
#     cur.close()
#     conn.close()

# @task
# def load_into_postgres(df):
#     '''
#     Loads the transformed data passed in as a DataFrame
#     into the 'cpd_incidents' table in our Postgres instance.
#     '''
#     # create table to insert data into as necessary
#     create_postgres_table()

#     # create Engine object to connect to DB
#     engine = create_engine())

#     # # insert data into Postgres DB into the 'cpd_incidents' table
#     # df.to_sql('cpd_incidents', engine, if_exists='replace')


if __name__ == "__main__":
    try:
        # prefect cloud
        # etl()
        # local deployement
        etl.serve(
            name="consume-energy",
            cron="*/1 * * * *",  # tous les jours à 6h UTC
            tags=["energy", "etl"],
            description="Daily energy consumption ETL and ML.",
            pause_on_shutdown=False,
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")


# Deploiement directement dans le script python
#  if __name__ == "__main__":
#     try:
#         etl.deploy(
#             name="consume-energy",
#             work_pool_name="energy-pool",   # ⚠️ doit exister sur ton serveur Prefect
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
