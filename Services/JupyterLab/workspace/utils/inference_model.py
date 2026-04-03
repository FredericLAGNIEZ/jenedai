"""
Gestion de l'inférence du modèle en production via MLflow
"""
import logging
import mlflow
import mlflow.sklearn
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InferenceModel:
    """Classe pour charger et utiliser un modèle en production"""
    
    def __init__(self, mlflow_tracking_uri, experiment_name):
        """
        Initialise la connexion MLflow
        
        Args:
            mlflow_tracking_uri: URI du serveur MLflow
            experiment_name: Nom de l'expérience MLflow
        """
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.experiment_name = experiment_name
        self.model = None
        self.model_version = None
        
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        logger.info(f"MLflow connecté à {mlflow_tracking_uri}")
    
    def load_production_model(self, model_name, alias_prod="prod"):
        """
        Charge le modèle en production depuis MLflow via Alias
        
        Args:
            model_name: Nom du modèle dans MLflow
            alias_prod: Alias pour la production (défaut: "prod")
            
        Returns:
            Modèle chargé ou None en cas d'erreur
        """
        try:
            # Récupérer la version avec l'alias prod
            client = mlflow.tracking.MlflowClient()
            model_version = client.get_model_version_by_alias(model_name, alias_prod)
            
            if not model_version:
                logger.error(f"Aucune version avec l'alias '{alias_prod}' pour {model_name}")
                return False
            
            self.model_version = model_version.version
            
            # Charger le modèle via alias
            model_uri = f"models:/{model_name}@{alias_prod}"
            self.model = mlflow.sklearn.load_model(model_uri)
            
            logger.info(f"Modèle {model_name} v{self.model_version} chargé via alias '{alias_prod}'")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            return False
    
    def predict(self, X_data):
        """
        Génère des prédictions
        
        Args:
            X_data: Features pour la prédiction (DataFrame ou array)
            
        Returns:
            Prédictions et scores de confiance
        """
        if self.model is None:
            logger.error("Modèle non chargé")
            return None, None
        
        try:
            predictions = self.model.predict(X_data)
            
            # Essayer de récupérer les scores de confiance
            confidence_scores = None
            if hasattr(self.model, 'predict_proba'):
                confidence_scores = self.model.predict_proba(X_data).max(axis=1)
            elif hasattr(self.model, 'decision_function'):
                confidence_scores = np.abs(self.model.decision_function(X_data))
            
            logger.info(f"Prédictions générées pour {len(X_data)} échantillons")
            return predictions, confidence_scores
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {str(e)}")
            return None, None
    
    def get_model_info(self):
        """Retourne les informations du modèle chargé"""
        if self.model is None:
            return None
        
        return {
            "model_type": type(self.model).__name__,
            "version": self.model_version,
            "n_features": getattr(self.model, 'n_features_in_', 'unknown')
        }
