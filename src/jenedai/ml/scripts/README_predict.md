# Flow Prefect — Test de prédiction Jenedai

## Vue d'ensemble

Ce flow sert de **script de test manuel** pour valider qu'un modèle enregistré dans MLflow (alias `champion`) charge correctement et produit une prédiction cohérente, sans passer par l'interface Gradio déployée sur Hugging Face Spaces.

Il génère un échantillon **synthétique aléatoire** (pas de données réelles) via `EnergyPredictor._generate_random_sample()`, et vérifie que le pipeline complet (préprocessing + modèle) répond sans erreur.

## Rôle dans le projet

|                          |                                                                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Usage**         | Test local / sanity check avant déploiement                                                                                         |
| **Ne sert pas à** | Servir des prédictions en production (c'est le rôle de l'API FastAPI + Space Gradio sur HF)                                        |
| **Fréquence**     | Lancement manuel, à la demande                                                                                                      |
| **Dépendance**    | Nécessite un accès à un serveur MLflow accessible (`MLFLOW_TRACKING_URI`) avec un modèle enregistré sous l'alias `champion` |

## Prérequis

- Un `.env` avec les variables :
  - `MLFLOW_TRACKING_URI`
  - `MLFLOW_S3_ENDPOINT_URL` (si l'artifact store est sur S3/Garage)
  - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
- Un modèle enregistré dans MLflow sous le nom défini dans `constants.MODEL_NAME`, avec l'alias `champion` pointant vers une version valide
- Le module `jenedai.ml.models.energy_predictor.EnergyPredictor` accessible via le `sys.path`

## Architecture du script

### `_setup()`

```python
def _setup():
    load_dotenv(override=True)
    src_path = Path(__file__).parents[3]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
```

Initialise l'environnement d'exécution :

- Charge les variables d'environnement (`.env`, avec `override=True` pour forcer la priorité sur les variables système existantes)
- Ajoute la racine du projet au `sys.path`, pour permettre l'import de `jenedai.ml.models.energy_predictor` peu importe le répertoire courant


## Flow

### `predict()`

Étapes :

1. **Chargement du pipeline MLflow**

   ```python
   mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
   pipeline = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
   ```

   Charge le pipeline complet (préprocessing + `RandomForestRegressor`) via l'alias `champion`, en `pyfunc` — cohérent avec le flavor utilisé pour l'export vers Hugging Face Hub dans `export_model.py`.
2. **Génération d'un échantillon synthétique**

   ```python
   predictor = EnergyPredictor()
   sample = predictor._generate_random_sample()
   ```

   `EnergyPredictor` est instancié uniquement pour accéder à sa méthode `_generate_random_sample()` — le modèle interne de `EnergyPredictor` (`self.model`, `self.preprocessor`) n'est **pas** utilisé ici ; seul le pipeline chargé depuis MLflow sert à la prédiction.
3. **Mise en forme et prédiction**

   ```python
   sample_df = pd.DataFrame([sample])[predictor.FEATURES]
   predicted = pipeline.predict(sample_df)
   ```

   Le DataFrame est explicitement réordonné selon `predictor.FEATURES` pour garantir la correspondance de colonnes attendue par le pipeline.
4. **Log du résultat**

   ```python
   logger.info(f"🤖 Prédit : {float(predicted[0]):,.0f} Wh")
   return float(predicted[0])
   ```

## Lien avec le déploiement Gradio / HF

Ce script valide **la même chaîne logique** que celle utilisée côté Gradio (Space HF) et côté API FastAPI :

| Étape                      | Ce script (test local)                           | Space Gradio / API (prod)                                                                                                     |
| --------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Chargement du modèle       | `mlflow.pyfunc.load_model` depuis MLflow local | `snapshot_download` depuis HF Hub + `mlflow.pyfunc.load_model`                                                            |
| Génération d'échantillon | `EnergyPredictor._generate_random_sample()`    | Listes de valeurs codées en dur (`SECTEURS`, `VILLES`, etc.) dans `app.py`, dérivées des mêmes catégories réelles |
| Prédiction                 | `pipeline.predict(sample_df)`                  | Identique                                                                                                                     |

**Utilité principale** : avant de relancer `export_model.py` pour pousser une nouvelle version du modèle vers HF Hub, ce script permet de vérifier en local que le modèle `champion` actuel dans MLflow charge et prédit correctement — évite de découvrir un problème de compatibilité une fois déployé sur HF.

## Exécution

### Lancement direct

```bash
uv run python predict.py
```

Affiche la prédiction dans les logs (`log_prints=True` fait remonter les `print()` éventuels dans les logs Prefect).

## Points de vigilance

- **`timeout_seconds=3600`** est large pour un simple appel de prédiction — hérité probablement d'un template Prefect commun au projet plutôt qu'un besoin réel de ce flow spécifique.
- **`MODEL_NAME`** vient de `constants.py` — s'assurer qu'il correspond bien au nom utilisé dans `config.yaml` (`model_registry.name`) pour l'export HF, afin d'éviter un cas où le test local valide un modèle différent de celui réellement exporté.
- **Échantillon synthétique uniquement** : ce test ne valide pas la cohérence du modèle sur des données réelles récentes — seulement que le pipeline s'exécute sans erreur technique (chargement, typage, colonnes). Pour une vraie validation de dérive/performance, voir le flow de monitoring (`monitor_task` avec Evidently).
