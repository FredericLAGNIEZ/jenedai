import os
import sys
from pathlib import Path

import pandas as pd

# Imports légers
from prefect import flow, get_run_logger


def _setup():
    """Initialisation unique au process principal."""
    from dotenv import load_dotenv

    load_dotenv(override=True)

    src_path = Path(__file__).parents[3]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    print("Python:", sys.executable)


FEATURES = [
    "secteur_activite",
    "plage_de_puissance_souscrite",
    "nb_points_soutirage",
    "ville",
    "en_vacances",  # ← une seule colonne 0 ou 1
    "temperature_2m_mean",
    "relative_humidity_mean",
    "precipitation_sum",
    "month",
    "jour_semaine",
]

TARGET = "total_energie_soutiree_wh"
#############################################################################################
# FLOW
#############################################################################################


@flow(
    name="consume_energy_predict",
    description="Predict pipeline for energy consumption data.",
    log_prints=True,
    timeout_seconds=3600,
)
def predict():
    """Main Pipeline entry"""
    import mlflow
    from constants import MODEL_NAME

    from jenedai.ml.models.energy_predictor import EnergyPredictor

    logger = get_run_logger()

    # Chargement du modèle MLflow
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    my_clf = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/7")
    logger.info("✅ Model loaded")

    # Génération d'un échantillon synthétique
    predictor = EnergyPredictor()
    sample = predictor._generate_random_sample()
    sample_df = pd.DataFrame([sample])
    logger.info(f"📋 Échantillon généré : {sample}")

    # Prédiction
    predicted = my_clf.predict(sample_df[predictor.FEATURES])
    logger.info(f"🤖 Prédit : {float(predicted[0]):,.0f} Wh")

    print(f"🤖 Prédit  : {float(predicted[0]):,.0f} Wh")
    return float(predicted[0])


#     try:
#         data_folder = Path("./data")
#         data_path = data_folder / "extract_cvs_engis_dataset.csv"

#         if data_path.exists():
#             logger.info(f"data_path exists: {data_path.exists()}")
#             logger.info(f"CSV size: {os.path.getsize(data_path) if data_path.exists() else 'NOT FOUND'}")
#         else:
#             logger.info(f"Contenu du dossier data: {list(Path(os.getcwd()).glob('data/*'))}")

#         logger.info("Extracting data from source...")
#         df_raw = load_data(logger, data_path)
#         logger.info(f"Extracted {len(df_raw)} rows, {len(df_raw.columns)} columns.")
#     except Exception as e:
#         msg = "Loading error on Data Pipeline"
#         logger.error(f" {msg} : {e}")
#         return


# # Remplacer tout le pipeline validate/cast/transform par :
# sample_row = generate_random_sample()
# predicted = my_clf.predict(sample_row[FEATURES])

# print(f"🤖 Prédit : {float(predicted[0]):,.0f} Wh")


if __name__ == "__main__":
    _setup()
    try:
        predict()
    #     predict.serve(
    #         #  name="consume-energy",
    #         #  cron="0 6 * * *",          # tous les jours à 6h UTC
    #         #  tags=["energy", "etl"],
    #         #  description="Daily energy consumption ETL and ML.",
    #         #  pause_on_shutdown=False,
    #         #  limit=1)
    #    )
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
