import sys
from pathlib import Path
import os


# src/jenedai/ml/scripts/test_prefect.py → remonte 3 niveaux → src/
src_path = Path(__file__).parents[3]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import traceback
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
# from prefect.blocks.notifications import SlackWebhook  # optionnel
from datetime import timedelta
import pandas as pd
from prefect.settings import PREFECT_API_URL
from jenedai.ml.utils.logs import configure_logging
from jenedai.ml.utils.get_console import get_console
from jenedai.ml.models.data_validator_jenedai import DataValidator
from jenedai.ml.models.data_caster_jenedai import DataCaster
from jenedai.ml.models.data_transformer_jenedai import Transformer
from jenedai.ml.models.load_data_jenedai import load_data
from prefect.runner.storage import GitRepository

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

# Chemin absolu relatif au script
data_folder = Path(__file__).parents[4] / "data"
data_path = data_folder / "extract_cvs_engis_dataset.csv "
# Chemin absolu relatif au script
logs_folder = Path(__file__).parents[4] / "logs"

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
    data_folder = Path(__file__).parents[3] / "data"
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
        name=f"ML Enedis",
        profile="basic",
    )
    logger.info("Système de logs configuré")
         
    # Data_pipeline : loading
    try:
        print(f"New new data_path : {data_path}")
        df = load_task(logger,str(data_path))
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


# if __name__ == "__main__":
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

if __name__ == "__main__":
    try:            
        etl()           
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")

