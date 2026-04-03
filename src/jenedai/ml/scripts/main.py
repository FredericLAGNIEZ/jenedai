from pathlib import Path
import argparse
import sys
import traceback
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.blocks.notifications import SlackWebhook  # optionnel
from datetime import timedelta
import pandas as pd
from prefect.settings import PREFECT_API_URL
from jenedai.ml.utils.logs import configure_logging
from jenedai.ml.utils.get_console import get_console
from jenedai.ml.models.data_validator_jenedai import DataValidator
from jenedai.ml.models.data_caster_jenedai import DataCaster
from jenedai.ml.models.data_transformer_jenedai import Transformer
from jenedai.ml.models.load_data_jenedai import load_data


# from prefect.settings import PREFECT_API_URL
# import os

from dotenv import load_dotenv
load_dotenv()

@task(
name="load",
retries=3,
retry_delay_seconds=60,
cache_key_fn=task_input_hash,
cache_expiration=timedelta(hours=1),
tags=["load"])
def load_task(logger, data_path: str) -> pd.DataFrame|None:
    try:
        df = load_data(logger, data_path)
        return df
    except Exception as e:
        msg = "Loading error on Data Pipeline"
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
    # Hors système de logging
    console = get_console()

    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]🔍 ML Enedis [/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]\n")

    logs_folder = "./logs"
    data_folder = "./data"
    
    # ✅ Système de logging
    logger = configure_logging(
        path_logs=logs_folder,
        name=f"ML Enedis",
        profile="basic",
    )

    logger.info("Système de logs configuré")

    # ✅ Parser d'arguments
    parser = argparse.ArgumentParser(
        description="ML Enedis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Exemples d'utilisation:
        python3 ....
        """,
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Ne pas exporter en JSON (garder uniquement le JSONL)",
    )

    # args = parser.parse_args()
        
    # Data_pipeline : loading
    data_path = Path(data_folder) /"extract_cvs_engis_dataset_500000.csv"
    try:
        df = load_task(logger, data_path)
        # ✅ Version défensive complète
        if df is None:
            raise ValueError("load_data n'a retourné aucune donnée.")
        if df.empty:
            raise ValueError("Le DataFrame chargé est vide.")
        else:
            console.print("✓ Data loaded\n")
    except Exception as e:
        logger.error(f"ETL failed: {e}")
        raise 

    # # Data_pipeline : validation
    # try:
    #     dataValidator = DataValidator()
    #     df = dataValidator.validate(logger, df)
    #     console.print("✓ Data Validated\n")
    #     console.print(f"✓ DataFrame has now {df.shape[0]} lines\n")

    # except Exception as e:
    #     msg = "DataValidation Error Data Pipeline"
    #     logger.error(f" {msg} : {e}")
    #     return 1


    # #Extraction en Masse
    # try:
    #     extracteur_factures.extraire_toutes()
    # except Exception as e:
    #     msg = "Erreur lors de l'extraction par ExtracteurFacture"
    #     logger.error(f" {type(e)} {msg} : {e}")
    #     return 1

    # # Affichage global
    # try:
    #     extracteur_factures.display_all()
    # except Exception as e:
    #     msg = "Erreur lors de l'affichage de ExtracteurParDossier"
    #     logger.error(f" {type(e)} {msg} : {e}")
    #     return 1

    # # #Passage en CSV
    # # try:
    # #     extracteur_factures.to_csv()
    # # except Exception as e:
    # #     msg = "Erreur lors du passage en CSV de ExtracteurParDossier"
    # #     logger.error(f" {type(e)} {msg} : {e}")
    # #     return 1


if __name__ == "__main__":
    try:            
        etl.deploy(
            name="consume-energy",
            work_pool_name="energy-pool",   # ⚠️ doit exister sur ton serveur Prefect
            cron="*/5 * * * *",
            tags=["energy", "etl"],
            description="Daily energy consumption ETL and ML.")            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")



# if __name__ == "__main__":
#     try:            
#         etl.serve(
#             name="consume-energy",
#             cron="*/1 * * * *",          # tous les jours à 6h UTC
#             tags=["energy", "etl"],
#             description="Daily energy consumption ETL and ML.",
#             pause_on_shutdown=False)
#     except KeyboardInterrupt:
#         print("\n\n⚠️  Interruption utilisateur")
#     except Exception as e:
#         print(f"\n❌ Erreur fatale: {e}")

