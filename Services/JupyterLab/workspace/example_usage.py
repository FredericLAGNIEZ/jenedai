"""
Exemple d'utilisation complet du pipeline MLOps
À exécuter dans un notebook Jupyter
"""

# %% 1. IMPORTER LES MODULES
from utils.pipeline import MLPipeline
from utils.data_loader import load_config
import logging

logging.basicConfig(level=logging.INFO)

# %% 2. INITIALISER LE PIPELINE
print("\n>>> Initialisation du pipeline...\n")
pipeline = MLPipeline(config_path="utils/config.yaml")

# %% 3. EXÉCUTER LE PIPELINE COMPLET
# Note: Remplacer "data/raw/extract_cvs_engis_dataset.csv" par votre fichier de données
file_path = "data/extract_cvs_engis_dataset.csv"
""" print("\n>>> Lancement du pipeline complet...\n")
success = pipeline.run_full_pipeline(file_path)

if success:
    print("\n✓ Pipeline exécuté avec succès!")
    print(f"\nMétriques finales: {pipeline.metrics}")
else:
    print("\n✗ Erreur lors de l'exécution du pipeline") """

# %% 4. ALTERNATIVE: EXÉCUTER ÉTAPE PAR ÉTAPE
print("\n" + "="*50)
print("EXÉCUTION ÉTAPE PAR ÉTAPE (alternative)")
print("="*50)

pipeline2 = MLPipeline()

print("\n1. Chargement des données...")
pipeline2.step_1_load_data(file_path)

print("\n2. Validation des données...")
pipeline2.step_2_validate_data(save_report=True)

print("\n3. Préparation des données...")
pipeline2.step_3_prepare_data()

print("\n4. Entraînement du modèle...")
pipeline2.step_4_train_model()

print("\n5. Évaluation du modèle...")
pipeline2.step_5_evaluate_model()
# Afficher les métriques
if pipeline2.metrics:
    print("\n--- RÉSULTATS ---")
    for key, value in pipeline2.metrics.items():
        print(f"  {key}: {value:.4f}")

print("\n6. Monitoring de la performance...")
pipeline2.step_6_monitor_performance()

print("\n7. Logging avec MLflow...")
pipeline2.step_7_log_with_mlflow()

print("\n✓ Pipeline étape par étape terminé!")

# %%
