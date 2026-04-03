"""
Suivi des expériences avec MLflow
"""
import mlflow
import mlflow.sklearn
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_mlflow_tracking(tracking_uri):
    """Configure la cible de suivi MLflow"""
    try:
        mlflow.set_tracking_uri(tracking_uri)
        logger.info(f"Tracking URI configuré: {tracking_uri}")
    except Exception as e:
        logger.error(f"Erreur lors de la configuration MLflow: {e}")


def start_mlflow_run(experiment_name, run_name=None):
    """
    Démarre une nouvelle run MLflow
    
    Args:
        experiment_name: Nom de l'expérience
        run_name: Nom de la run (optionnel)
    """
    try:
        mlflow.set_experiment(experiment_name)
        mlflow.start_run(run_name=run_name)
        logger.info(f"Run MLflow démarrée - Expérience: {experiment_name}")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de la run: {e}")


def log_params(params):
    """Enregistre les paramètres"""
    try:
        mlflow.log_params(params)
        logger.info(f"Paramètres enregistrés: {params}")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement des paramètres: {e}")


def log_metrics(metrics):
    """Enregistre les métriques"""
    try:
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        logger.info(f"Métriques enregistrées: {list(metrics.keys())}")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement des métriques: {e}")


def log_model(model, artifact_path="model"):
    """Enregistre le modèle"""
    try:
        mlflow.sklearn.log_model(model, artifact_path)
        logger.info(f"Modèle enregistré: {artifact_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du modèle: {e}")


def log_artifact(file_path, artifact_path=None):
    """Enregistre un artefact (fichier)"""
    try:
        mlflow.log_artifact(file_path, artifact_path)
        logger.info(f"Artefact enregistré: {file_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'artefact: {e}")


def end_mlflow_run():
    """Termine la run MLflow courante"""
    try:
        mlflow.end_run()
        logger.info("Run MLflow terminée")
    except Exception as e:
        logger.error(f"Erreur lors de la terminaison de la run: {e}")


def log_training_session(model, metrics, params, artifact_path="model", experiment_name="default", tracking_uri=None):
    """
    Fonction utilitaire pour enregistrer une session complète
    
    Args:
        model: Modèle entraîné
        metrics: Dict de métriques
        params: Dict de paramètres
        artifact_path: Chemin de sauvegarde du modèle
        experiment_name: Nom de l'expérience
        tracking_uri: URI de suivi MLflow (par défaut: http://localhost:5000)
    """
    try:
        if tracking_uri is None:
            tracking_uri = "http://localhost:5000"
        set_mlflow_tracking(tracking_uri)
        start_mlflow_run(experiment_name)
        log_params(params)
        log_metrics(metrics)
        log_model(model, artifact_path)
        end_mlflow_run()
        logger.info("Session d'entraînement enregistrée dans MLflow")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la session: {e}")


# ============= GESTION DES ALIASES MLFLOW =============

def register_model_version(model_name, run_id, artifact_path="model", description=None):
    """
    Enregistre une version de modèle dans le Model Registry
    
    Args:
        model_name: Nom du modèle dans le registry
        run_id: ID de la run MLflow qui contient le modèle
        artifact_path: Chemin de l'artefact du modèle
        description: Description du modèle (optionnel)
        
    Returns:
        ModelVersion ou None en cas d'erreur
    """
    try:
        client = mlflow.tracking.MlflowClient()
        model_uri = f"runs:/{run_id}/{artifact_path}"
        
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name,
            description=description
        )
        
        logger.info(f"Modèle {model_name} v{model_version.version} enregistré dans le registry")
        return model_version
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du modèle: {e}")
        return None


def set_model_alias(model_name, version, alias):
    """
    Définit un alias pour une version de modèle
    
    Args:
        model_name: Nom du modèle
        version: Version du modèle
        alias: Alias à attribuer (ex: "prod", "staging", "test")
        
    Returns:
        True si succès, False sinon
    """
    try:
        client = mlflow.tracking.MlflowClient()
        client.set_registered_model_alias(
            name=model_name,
            alias=alias,
            version=version
        )
        
        logger.info(f"Alias '{alias}' assigné à {model_name} v{version}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'assignation de l'alias: {e}")
        return False


def get_model_version_by_alias(model_name, alias):
    """
    Récupère la version d'un modèle pour un alias spécifique
    
    Args:
        model_name: Nom du modèle
        alias: Alias à chercher (ex: "prod", "staging")
        
    Returns:
        ModelVersion ou None si non trouvé
    """
    try:
        client = mlflow.tracking.MlflowClient()
        model_version = client.get_model_version_by_alias(model_name, alias)
        return model_version
        
    except Exception as e:
        logger.warning(f"Alias '{alias}' non trouvé pour {model_name}: {e}")
        return None


def list_model_aliases(model_name):
    """
    Liste tous les aliases d'un modèle
    
    Args:
        model_name: Nom du modèle
        
    Returns:
        Dict {alias: version} ou {} si aucun
    """
    try:
        client = mlflow.tracking.MlflowClient()
        model = client.get_registered_model(model_name)
        
        # Construire un dict {alias: version}
        aliases_dict = {}
        if model.aliases:
            for alias, version in model.aliases.items():
                aliases_dict[alias] = version
        
        return aliases_dict
        
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des aliases: {e}")
        return {}


def compare_model_metrics(model_name, version_new, alias_current="prod", metric_keys=None):
    """
    Compare les métriques de deux versions de modèle
    Support de plusieurs métriques avec priorité
    
    Args:
        model_name: Nom du modèle
        version_new: Version nouvelle (en Staging)
        version_current: Version courante (en Production) - optionnel
        metric_keys: Liste de métriques à chercher (priorité décroissante)
                    Ex: ["mae", "rmse", "mape", "accuracy"]
                    Par défaut: ["mae", "rmse", "accuracy"]
                    Les métriques doivent correspondre exactement aux noms dans MLflow
        
    Returns:
        Dict avec les métriques et le résultat de comparaison
    """
    try:
        # Métriques par défaut pour prédiction énergétique
        if metric_keys is None:
            metric_keys = ["mae", "rmse", "accuracy"]
        
        if isinstance(metric_keys, str):
            metric_keys = [metric_keys]
        
        client = mlflow.tracking.MlflowClient()
        
        # Récupérer les infos des versions
        model_version_new = client.get_model_version(model_name, version_new)
        run_id_new = model_version_new.run_id
        run_new = mlflow.get_run(run_id_new)
        
        # Chercher les métriques
        metrics_new = {}
        metric_used = None
        metric_value = None
        available_metrics = list(run_new.data.metrics.keys()) if run_new.data.metrics else []
        
        logger.info(f"  → Métriques disponibles pour v{version_new}: {available_metrics}")
        
        # Essayer chaque métrique directement
        for metric_key in metric_keys:
            if metric_key in run_new.data.metrics:
                value = run_new.data.metrics[metric_key]
                metrics_new[metric_key] = value
                
                # Première métrique trouvée = celle à utiliser pour la comparaison
                if metric_used is None:
                    metric_used = metric_key
                    metric_value = value
                
                logger.info(f"    ✓ {metric_key} = {value:.4f}")
        
        # Récupérer la version courante par alias
        model_version_current = get_model_version_by_alias(model_name, alias_current)
        
        if model_version_current is None:
            logger.warning(f"  ! Alias '{alias_current}' non trouvé (première promotion)")
            return {
                "metrics_new": metrics_new,
                "metrics_current": {},
                "is_better": True,
                "metric_used": metric_used,
                "improvement": None,
                "improvement_pct": None,
                "alias_current": alias_current
            }
        
        # Récupérer les métriques de la version courante
        run_id_current = model_version_current.run_id
        run_current = mlflow.get_run(run_id_current)
        
        metrics_current = {}
        metric_current_value = None
        available_metrics_current = list(run_current.data.metrics.keys()) if run_current.data.metrics else []
        
        logger.info(f"  → Métriques disponibles pour v{model_version_current.version} ({alias_current}): {available_metrics_current}")
        
        for metric_key in metric_keys:
            if metric_key in run_current.data.metrics:
                value = run_current.data.metrics[metric_key]
                metrics_current[metric_key] = value
                
                if metric_key == metric_used:
                    metric_current_value = value
                
                logger.info(f"    ✓ {metric_key} = {value:.4f}")
        # Comparer sur la métrique sélectionnée
        is_better = False
        improvement = None
        improvement_pct = None
        
        if metric_value is not None and metric_current_value is not None:
            improvement = metric_value - metric_current_value
            
            # Pour MAE/RMSE/MAPE plus petit c'est mieux (négatif = amélioration)
            # Pour accuracy/R2 plus grand c'est mieux (positif = amélioration)
            if "mae" in metric_used or "rmse" in metric_used or "error" in metric_used:
                is_better = improvement < 0  # Réduction d'erreur = mieux
                improvement_pct = (abs(improvement) / abs(metric_current_value)) * 100 if metric_current_value != 0 else 0
            else:
                is_better = improvement > 0  # Augmentation de score = mieux
                improvement_pct = (improvement / abs(metric_current_value)) * 100 if metric_current_value != 0 else 0
                
        elif metric_value is not None:
            is_better = True
        
        result = {
            "metrics_new": metrics_new,
            "metrics_current": metrics_current,
            "is_better": is_better,
            "improvement": improvement,
            "improvement_pct": improvement_pct,
            "metric_used": metric_used,
            "version_new": version_new,
            "version_current": model_version_current.version,
            "alias_current": alias_current
        }
        
        # Log de comparaison
        if metric_used and improvement is not None:
            symbol = "📉" if improvement < 0 else "📈"
            logger.info(f"  {symbol} Comparaison {model_name}: {metric_used} {improvement:+.4f} ({improvement_pct:+.1f}%)")
        else:
            logger.info(f"  ⚠️  Comparaison {model_name}: Comparison impossible (métrique manquante)")
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def promote_model_to_production(model_name, version, alias_prod="prod", metric_keys=None, min_improvement=0.0):
    """
    Promeut automatiquement un modèle en Production via Alias
    Support de plusieurs métriques avec priorité
    
    Args:
        model_name: Nom du modèle
        version: Version à promouvoir
        alias_prod: Alias pour la production (défaut: "prod")
        metric_keys: Métrique(s) de validation (str ou list)
                    Ex: "mae" ou ["mae", "rmse", "accuracy"]
                    Par défaut: ["mae", "rmse", "accuracy"] pour prédiction énergétique
        min_improvement: Amélioration minimale requise en % (défaut: 0.0)
        
    Returns:
        Dict avec le résultat de la promotion
    """
    try:
        logger.info(f"=== PROMOTION EN PRODUCTION: {model_name} v{version} ===")
        
        # Normaliser metric_keys - support list ou str
        metric_keys_normalized = metric_keys if isinstance(metric_keys, list) else [metric_keys] if metric_keys else ["mae", "rmse", "accuracy"]
        
        # Comparer avec la version courante en prod
        comparison = compare_model_metrics(model_name, version, alias_current=alias_prod, metric_keys=metric_keys_normalized)
        
        if comparison is None:
            logger.error("Impossible de comparer les modèles")
            return {"success": False, "reason": "comparison_failed"}
        
        logger.info(f"Métrique utilisée: {comparison['metric_used']}")
        
        # Afficher toutes les métriques trouvées
        if comparison['metrics_new']:
            logger.info("Métriques nouvelle version:")
            for key, val in comparison['metrics_new'].items():
                logger.info(f"  • {key}: {val:.4f}")
        
        if comparison['metrics_current']:
            logger.info(f"Métriques version avec alias '{alias_prod}':")
            for key, val in comparison['metrics_current'].items():
                logger.info(f"  • {key}: {val:.4f}")
        
        # Vérifier si on doit promouvoir
        if not comparison["is_better"]:
            logger.warning(f"Modèle v{version} pas assez bon pour la production")
            return {
                "success": False,
                "reason": "model_not_better",
                "improvement": comparison["improvement"],
                "improvement_pct": comparison.get("improvement_pct"),
                "metric_used": comparison["metric_used"]
            }
        
        # Vérifier l'amélioration minimale
        improvement_pct = comparison.get("improvement_pct")
        if improvement_pct is not None and abs(improvement_pct) < min_improvement:
            logger.warning(f"Amélioration insuffisante: {improvement_pct:.1f}% < {min_improvement}%")
            return {
                "success": False,
                "reason": "insufficient_improvement",
                "improvement": comparison["improvement"],
                "improvement_pct": improvement_pct,
                "metric_used": comparison["metric_used"]
            }
        
        # Assigner l'alias Production
        try:
            set_model_alias(model_name, version, alias_prod)
            logger.info(f"✓ Modèle {model_name} v{version} assigné à l'alias '{alias_prod}'")
        except Exception as e:
            logger.error(f"Erreur lors de l'assignation de l'alias: {e}")
            return {"success": False, "reason": "alias_assignment_failed", "error": str(e)}
        
        return {
            "success": True,
            "version": version,
            "alias_prod": alias_prod,
            "improvement": comparison["improvement"],
            "improvement_pct": comparison.get("improvement_pct"),
            "metric_used": comparison["metric_used"],
            "metrics_new": comparison["metrics_new"]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la promotion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "reason": str(e)}


def delete_model_alias(model_name, alias):
    """
    Supprime un alias d'un modèle
    
    Args:
        model_name: Nom du modèle
        alias: Alias à supprimer
        
    Returns:
        True si succès, False sinon
    """
    try:
        client = mlflow.tracking.MlflowClient()
        client.delete_registered_model_alias(name=model_name, alias=alias)
        logger.info(f"Alias '{alias}' supprimé de {model_name}")
        return True
    except Exception as e:
        logger.warning(f"Impossible de supprimer l'alias '{alias}': {e}")
        return False
