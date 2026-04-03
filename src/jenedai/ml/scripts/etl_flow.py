
# # https://towardsdatascience.com/creating-a-data-pipeline-to-monitor-local-crime-trends/


# @flow(
#     name="consume_energy_etl", log_prints=True
# )  # Our pipeline will appear as 'consume_energy_etl' in the Prefect UI. All print outputs will be displayed in Prefect.
# def etl():
#     """
#     Execute the ETL pipeline:
#     - Extract 
#     - Validate and transform the extracted data to prepare it for storage
#     """
#     print("Extracting data...")
#     extracted_df = extract_data()

#     print("Performing data quality checks...")
#     validated_df = validate_data(extracted_df)

#     print("Performing data transformations...")
#     transformed_df = transform_data(validated_df)

#     print("Importing data into Postgres...")
#     load_into_postgres(transformed_df)

#     print("ETL complete!")


# if __name__ == "__main__":
#     etl.serve(name="cpd-pipeline-deployment", cron="0 0 * * *")

from pathlib import Path
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.blocks.notifications import SlackWebhook  # optionnel
from datetime import timedelta
import pandas as pd

#from jenedai.ml.utils.utils import find_project_directory
from jenedai.ml.models.data_validator_jenedai import DataValidator
from jenedai.ml.models.data_caster_jenedai import DataCaster
from jenedai.ml.models.data_transformer_jenedai import Transformer
from jenedai.ml.models.load_data_jenedai import load
# ─── Tasks ────────────────────────────────────────────────────────────────────

@task(
    name="load",
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["extract"],
)
def load_task() -> pd.DataFrame:
    logger = get_run_logger()
    logger.info("Extracting data from source...")
    df = load(path_file="../data/extract_cvs_engis_dataset_500000.csv")
    logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns.")
    return df


@task(
    name="validate",
    retries=1,
    retry_delay_seconds=30,
    tags=["quality"],
)
def validate_task(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    logger.info(f"Running data quality checks on {len(df)} rows...")
    dataValidator = DataValidator()
    validated_df = dataValidator.validate(df)
    logger.info("Validation passed.")
    return validated_df


# @task(
#     name="transform",
#     retries=1,
#     retry_delay_seconds=30,
#     tags=["transform"],
# )
# def transform_task(df: pd.DataFrame) -> pd.DataFrame:
#     logger = get_run_logger()
#     logger.info("Applying transformations...")
#     transformed_df = transform_data(df)
#     logger.info(f"Transformation complete. Output shape: {transformed_df.shape}")
#     return transformed_df


# @task(
#     name="load",
#     retries=3,
#     retry_delay_seconds=120,
#     tags=["load", "postgres"],
# )
# def load_task(df: pd.DataFrame) -> int:
#     logger = get_run_logger()
#     logger.info(f"Loading {len(df)} rows into Postgres...")
#     load_into_postgres(df)
#     logger.info("Load complete.")
#     return len(df)


# ─── Flow ─────────────────────────────────────────────────────────────────────

@flow(
    name="consume_energy_etl",
    description="ETL pipeline for energy consumption data.",
    log_prints=True,
    timeout_seconds=3600,  # 1h max — évite les runs bloqués
)
def etl():
    logger = get_run_logger()

    try:
        extracted_df  = load_task()
        validated_df  = validate_task(extracted_df)
        # transformed_df = transform_task(validated_df)
        # n_rows        = load_task(transformed_df)

        #logger.info(f"ETL complete — {n_rows} rows inserted.")

    except Exception as e:
        logger.error(f"ETL failed: {e}")

        # ── Notification Slack (décommenter si bloc configuré) ──
        # slack = SlackWebhook.load("slack-etl-alerts")
        # slack.notify(f"❌ consume_energy_etl failed: {e}")

        raise  # reraise pour que Prefect marque le run FAILED


# ─── Déploiement ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    etl.serve(
        name="consume-energy-etl-deployment",
        cron="0 6 * * *",          # tous les jours à 6h UTC
        tags=["energy", "etl"],
        description="Daily energy consumption ETL into Postgres.",
        pause_on_shutdown=False,
    )

# Ce qui a été ajouté et pourquoi
# Chaque étape est maintenant un @task séparé, ce qui apporte plusieurs avantages concrets :

# retries + retry_delay_seconds — l'extract et le load retentent 3 fois avec une pause, car ce sont les étapes les plus sensibles aux timeouts réseau/BDD.
# cache_key_fn=task_input_hash — si le flow re-tourne dans l'heure (ex. re-run manuel après un crash), l'extract ne rappelle pas l'API source inutilement.
# tags — permettent de filtrer les runs dans l'UI Prefect par étape ou par environnement.
# get_run_logger() — remplace les print() par le logger natif Prefect, visible directement dans l'UI avec le niveau (INFO / ERROR).
# timeout_seconds=3600 sur le flow — évite les runs bloqués indéfiniment si la BDD Postgres est injoignable.
# try/except avec raise — log l'erreur proprement et remonte l'exception pour que Prefect marque le run FAILED (sans ça, un flow qui catch sans re-raise apparaît COMPLETED même en cas d'échec).
# load_task retourne le nombre de lignes — utile pour des alertes si n_rows == 0 (extraction vide).

# Prochaine étape suggérée : ajouter un bloc Secret Prefect pour les credentials Postgres plutôt que de les mettre dans load.py en dur :
# pythonfrom prefect.blocks.system import Secret

# @task(name="load")
# def load_task(df: pd.DataFrame) -> int:
#     pg_url = Secret.load("postgres-url").get()
#     load_into_postgres(df, connection_string=pg_url)
#     return len(df)