# export_model.py
import os

import mlflow
import yaml
from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo

load_dotenv()

with open("config.yaml") as f:
    config = yaml.safe_load(f)

PROFILE = os.environ.get("PROFILE", config["default_profile"])
profile_config = config["profiles"][PROFILE]

MLFLOW_TRACKING_URI = profile_config["mlflow_tracking_uri"]
REGISTERED_MODEL_NAME = config["model_registry"]["name"]
MODEL_ALIAS = config["model_registry"]["alias"]
HF_REPO_ID = config["huggingface"]["repo_id"]
HF_TOKEN = os.environ[config["huggingface"]["token_env_var"]]


mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
MODEL_URI = f"models:/{REGISTERED_MODEL_NAME}@{MODEL_ALIAS}"
OUTPUT_DIR = "model_export"

if os.path.exists(OUTPUT_DIR):
    import shutil

    shutil.rmtree(OUTPUT_DIR)

# Le pipeline complet a été loggé avec mlflow.sklearn.log_model() côté training
model = mlflow.sklearn.load_model(MODEL_URI)
mlflow.sklearn.save_model(model, OUTPUT_DIR)
print(f"✅ Modèle exporté localement dans ./{OUTPUT_DIR} (profil: {PROFILE})")

# --- Upload vers HF Hub ---
api = HfApi(token=HF_TOKEN)
create_repo(repo_id=HF_REPO_ID, repo_type="model", exist_ok=True, token=HF_TOKEN)
api.upload_folder(
    folder_path=OUTPUT_DIR,
    repo_id=HF_REPO_ID,
    repo_type="model",
    token=HF_TOKEN,
)
print(f"✅ Modèle uploadé sur https://huggingface.co/{HF_REPO_ID}")


# pyfunc car le pipeline complet (preprocessing + RandomForest) est loggé ainsi
model = mlflow.pyfunc.load_model(MODEL_URI)
mlflow.pyfunc.save_model(path=OUTPUT_DIR, python_model=model._model_impl.python_model) if hasattr(
    model._model_impl, "python_model"
) else None
