"""
Entraînement et gestion du modèle
"""
import logging
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_model(X_train, y_train, model_type="random_forest", **kwargs):
    """
    Entraîne un modèle de machine learning
    
    Args:
        X_train: Features d'entraînement
        y_train: Target d'entraînement
        model_type: Type de modèle ('random_forest')
        **kwargs: Paramètres additionnels du modèle
    
    Returns:
        Modèle entraîné
    """
    try:
        # Vérifications préalables
        logger.info(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
        
        if X_train.shape[0] == 0 or len(y_train) == 0:
            logger.error(f"Données vides: X_train={X_train.shape}, y_train={y_train.shape}")
            return None
              
        if model_type == "random_forest":
            # Déterminer si c'est une classification ou régression
            unique_values = len(set(y_train))
            logger.info(f"Valeurs uniques dans y: {unique_values}")
            
            if unique_values < 20:  # Heuristique simple
                model = RandomForestClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    random_state=kwargs.get('random_state', 42),
                    n_jobs=-1
                )
                logger.info("Modèle de classification Random Forest créé")
            else:
                model = RandomForestRegressor(
                    n_estimators=kwargs.get('n_estimators', 100),
                    random_state=kwargs.get('random_state', 42),
                    n_jobs=-1
                )
                logger.info("Modèle de régression Random Forest créé")
        else:
            if(True):#model_type == "linear_regression"):
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                logger.info("Modèle de régression Linéaire créé")
            else:
                logger.error(f"Type de modèle non supporté: {model_type}")
                return None
        
        # Entraîner le modèle
        model.fit(X_train, y_train)
        logger.info("Modèle entraîné avec succès")
        
        return model
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def evaluate_model(model, X_test, y_test):
    """
    Évalue les performances du modèle
    
    Args:
        model: Modèle entraîné
        X_test: Features de test
        y_test: Target de test
    
    Returns:
        dict: Métriques d'évaluation
    """
    try:
        predictions = model.predict(X_test)
        
        metrics = {}
        
        # Vérifier si classification ou régression
        if hasattr(model, 'predict_proba'):  # Classification
            metrics['accuracy'] = accuracy_score(y_test, predictions)
            metrics['precision'] = precision_score(y_test, predictions, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_test, predictions, average='weighted', zero_division=0)
            metrics['f1'] = f1_score(y_test, predictions, average='weighted', zero_division=0)
            logger.info(f"Classification - Accuracy: {metrics['accuracy']:.3f}, F1: {metrics['f1']:.3f}")
        else:  # Régression
            metrics['mse'] = mean_squared_error(y_test, predictions)
            metrics['rmse'] = metrics['mse'] ** 0.5
            metrics['r2'] = r2_score(y_test, predictions)
            logger.info(f"Régression - RMSE: {metrics['rmse']:.3f}, R²: {metrics['r2']:.3f}")
        
        return metrics
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation: {e}")
        return None


# Note: Sauvegarde du modèle gérée par MLflow avec mlflow.sklearn.log_model()
# Voir mlflow_tracker.py pour les détails


def get_feature_importance(model, feature_names=None):
    """
    Obtient l'importance des features
    """
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            
            if feature_names is None:
                feature_names = [f"Feature_{i}" for i in range(len(importances))]
            
            # Créer un dictionnaire trié
            importance_dict = {name: imp for name, imp in zip(feature_names, importances)}
            importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
            logger.info("Features importances calculées")
            return importance_dict
        else:
            logger.warning("Le modèle n'a pas d'attribut 'feature_importances_'")
            return None
    except Exception as e:
        logger.error(f"Erreur lors du calcul des importances: {e}")
        return None
