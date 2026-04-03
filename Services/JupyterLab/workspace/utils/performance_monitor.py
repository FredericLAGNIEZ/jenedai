"""
Monitoring de la performance du modèle avec Evidently AI
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_performance_report(
    reference_data,
    current_data,
    predictions_ref,
    predictions_current,
    output_path="outputs/evidently_performance.html",
    target_column=None,
    problem_type="classification"
):
    """
    Création d'un rapport de performance avec détection de drift
    
    Args:
        reference_data: DataFrame de référence
        current_data: DataFrame courant
        predictions_ref: Prédictions sur les données de référence
        predictions_current: Prédictions sur les données courantes
        output_path: Chemin pour sauvegarder le rapport
        target_column: Nom de la colonne cible
        problem_type: Type de problème ('classification' ou 'regression')
    
    Returns:
        dict: Rapport de performance
    """
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Essayer d'utiliser Evidently si disponible
        try:
            from evidently.report import Report
            
            # Ajouter les prédictions aux données
            ref_with_pred = reference_data.copy()
            ref_with_pred['predictions'] = predictions_ref
            
            current_with_pred = current_data.copy()
            current_with_pred['predictions'] = predictions_current
            
            # Créer le rapport
            report = Report(metrics=[])
            # Laisser Evidently configurer automatiquement
            report.run(reference_data=ref_with_pred, current_data=current_with_pred)
            report.save_html(output_path)
            logger.info(f"Rapport Evidently créé: {output_path}")
            return report
        except (ImportError, AttributeError):
            # Fallback - créer un rapport HTML simple
            logger.warning("Evidently API non disponible, utilisation de rapport simple")
            return generate_simple_performance_report(
                reference_data, current_data, 
                predictions_ref, predictions_current,
                output_path, problem_type
            )
    except Exception as e:
        logger.error(f"Erreur lors de la création du rapport de performance: {e}")
        return None


def generate_simple_performance_report(
    reference_data,
    current_data,
    predictions_ref,
    predictions_current,
    output_path,
    problem_type
):
    """
    Génère un rapport HTML simple de performance (fallback)
    """
    try:
        # Calculer les statistiques de drift
        drift_info = detect_prediction_drift(predictions_ref, predictions_current)
        
        # Générer HTML
        html_content = """
        <html>
        <head><title>Rapport de Performance</title></head>
        <body>
        <h1>Rapport de Performance du Modèle</h1>
        """
        
        html_content += f"<h2>Type de problème: {problem_type}</h2>"
        
        # Informations de drift
        if drift_info:
            html_content += "<h3>Détection de Drift</h3>"
            html_content += f"<p><strong>Drift détecté:</strong> {drift_info['drift_detected']}</p>"
            html_content += f"<p><strong>Mean Drift:</strong> {drift_info['mean_drift']:.4f}</p>"
            html_content += f"<p><strong>Std Drift:</strong> {drift_info['std_drift']:.4f}</p>"
            html_content += f"<p><strong>Moyenne prédictions (ref):</strong> {drift_info['ref_mean']:.4f}</p>"
            html_content += f"<p><strong>Moyenne prédictions (current):</strong> {drift_info['current_mean']:.4f}</p>"
        
        html_content += "</body></html>"
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Rapport simple créé: {output_path}")
        return {"status": "success", "path": output_path}
    except Exception as e:
        logger.error(f"Erreur lors de la création du rapport simple: {e}")
        return None


def detect_prediction_drift(predictions_ref, predictions_current, threshold=0.1):
    """
    Détecte un changement de distribution dans les prédictions
    
    Args:
        predictions_ref: Prédictions de référence
        predictions_current: Prédictions courantes
        threshold: Seuil de drift
    
    Returns:
        dict: Résultats de la détection
    """
    try:
        # Calculer les statistiques
        ref_mean = np.mean(predictions_ref)
        current_mean = np.mean(predictions_current)
        
        ref_std = np.std(predictions_ref)
        current_std = np.std(predictions_current)
        
        # Drift sur la moyenne
        mean_drift = abs(current_mean - ref_mean) / (ref_mean + 1e-10)
        
        # Drift sur l'écart-type
        std_drift = abs(current_std - ref_std) / (ref_std + 1e-10)
        
        drift_detected = mean_drift > threshold or std_drift > threshold
        
        results = {
            'mean_drift': mean_drift,
            'std_drift': std_drift,
            'drift_detected': drift_detected,
            'ref_mean': ref_mean,
            'current_mean': current_mean,
            'ref_std': ref_std,
            'current_std': current_std
        }
        
        if drift_detected:
            logger.warning(f"Drift détecté! Mean drift: {mean_drift:.4f}, Std drift: {std_drift:.4f}")
        else:
            logger.info("Pas de drift détecté")
        
        return results
    except Exception as e:
        logger.error(f"Erreur lors de la détection du drift: {e}")
        return None


def monitor_model_performance(
    y_pred,
    y_actual,
    metrics_dict=None,
    problem_type="classification"
):
    """
    Monitoring continu de la performance du modèle
    
    Args:
        y_pred: Prédictions du modèle
        y_actual: Valeurs réelles
        metrics_dict: Dict existant de métriques (optionnel)
        problem_type: Type de problème
    
    Returns:
        dict: Métriques de performance
    """
    try:
        if metrics_dict is None:
            metrics_dict = {}
        
        if problem_type == "classification":
            from sklearn.metrics import accuracy_score, balanced_accuracy_score
            metrics_dict['accuracy'] = accuracy_score(y_actual, y_pred)
            metrics_dict['balanced_accuracy'] = balanced_accuracy_score(y_actual, y_pred)
            
        else:
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            metrics_dict['mae'] = mean_absolute_error(y_actual, y_pred)
            metrics_dict['mse'] = mean_squared_error(y_actual, y_pred)
            metrics_dict['rmse'] = np.sqrt(metrics_dict['mse'])
            metrics_dict['r2'] = r2_score(y_actual, y_pred)
        
        logger.info(f"Métriques de performance calculées: {metrics_dict}")
        return metrics_dict
        
    except Exception as e:
        logger.error(f"Erreur lors du monitoring: {e}")
        return None


def generate_monitoring_summary(drift_results, performance_metrics):
    """
    Génère un résumé du monitoring
    
    Args:
        drift_results: Résultats de la détection de drift
        performance_metrics: Métriques de performance
    
    Returns:
        str: Résumé formaté
    """
    summary = "=== MONITORING SUMMARY ===\n"
    
    if drift_results:
        summary += f"\n[DRIFT DETECTION]\n"
        summary += f"Drift detected: {drift_results['drift_detected']}\n"
        summary += f"Mean drift: {drift_results['mean_drift']:.4f}\n"
        summary += f"Std drift: {drift_results['std_drift']:.4f}\n"
    
    if performance_metrics:
        summary += f"\n[PERFORMANCE METRICS]\n"
        for key, value in performance_metrics.items():
            summary += f"{key}: {value:.4f}\n"
    
    logger.info(summary)
    return summary
