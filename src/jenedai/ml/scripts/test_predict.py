import os
import sys
from pathlib import Path

import pandas as pd


def _setup():
    """Initialisation unique au process principal."""
    from dotenv import load_dotenv

    load_dotenv(override=True)

    src_path = Path(__file__).parents[3]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    print("Python:", sys.executable)


_setup()

FEATURES = [
    "secteur_activite",
    "plage_de_puissance_souscrite",
    "nb_points_soutirage",
    "ville",
    "en_vacances",
    "temperature_2m_mean",
    "relative_humidity_mean",
    "precipitation_sum",
    "month",
    "jour_semaine",
]

TARGET = "total_energie_soutiree_wh"

# Variables S3 pour MLflow
os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ.get("MLFLOW_S3_ENDPOINT_URL", "")
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

#############################################################################################
# FLOW
#############################################################################################


def predict():
    """Main Pipeline entry"""
    import mlflow
    from constants import MODEL_NAME

    from jenedai.ml.models.energy_predictor import EnergyPredictor

    # Charger le pipeline complet (préprocessor + modèle)
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    pipeline = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
    # pipeline = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/15")  # Charge le pipeline complet
    print("✅ Pipeline (preprocessor + model) loaded")

    sklearn_pipeline = pipeline._model_impl.sklearn_model
    preprocessor = sklearn_pipeline.named_steps["Preprocessing"]
    cat_transformer = preprocessor.named_transformers_["cat"]
    encoder = cat_transformer.named_steps["encoder"]
    categorical_cols = preprocessor.transformers_[1][2]

    # # for col, cats in zip(categorical_cols, encoder.categories_):
    # #     print(f"{col}: {list(cats)}")

    # # Associer chaque colonne catégorielle à ses catégories
    # categories_by_col = dict(zip(categorical_cols, encoder.categories_))

    # # Isoler celles de "ville"
    # model_villes = list(categories_by_col["ville"])

    print("categorical_cols:", categorical_cols)
    print(
        "Colonne à l'index 3 :",
        categorical_cols[3] if len(categorical_cols) > 3 else "n'existe pas",
    )

    # Générer un échantillon synthétique avec EnergyPredictor
    predictor = EnergyPredictor()  # On utilise uniquement _generate_random_sample()
    sample = predictor._generate_random_sample()

    print("sample : ", sample)

    # Convertir l'échantillon en DataFrame avec les bonnes colonnes
    sample_df = pd.DataFrame([sample])[predictor.FEATURES]

    # 4. Prédire avec le pipeline
    predicted = pipeline.predict(sample_df)
    print(f"🤖 Prédit : {float(predicted[0]):,.0f} Wh")

    return float(predicted[0])


if __name__ == "__main__":
    try:
        predict()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")


## TEsts

#  # Récupérer le dernier run du modèle
#     client = MlflowClient()
#     experiment = client.get_experiment_by_name("energy_predictor")
#     runs = client.search_runs(
#         experiment_ids=[experiment.experiment_id],
#         filter_string="tags.mlflow.runName = 'energy_predictor'",
#         max_results=1
#     )
#     if not runs:
#         raise RuntimeError("Aucun run trouvé pour le modèle.")

#     run_id = runs[0].info.run_id

#     # Charger le modèle et le préprocessor
#     model_uri = f"runs:/{run_id}/random_forest"
#     preprocessor_uri = f"runs:/{run_id}/preprocessor"

#     model = mlflow.pyfunc.load_model(model_uri)
#     preprocessor = mlflow.pyfunc.load_model(preprocessor_uri)

#     logger.info("✅ Model and preprocessor loaded")

# ## Initialiser le prédicteur
# predictor = EnergyPredictor()
# predictor.model = model  # Chargement modèle
# predictor.preprocessor = preprocessor


# # Old way : Chargement du modèle MLflow (fonctionne)
# mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
# model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/7")
# logger.info("✅ Model loaded")
