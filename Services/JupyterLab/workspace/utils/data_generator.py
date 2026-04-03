"""
Génération de données pour l'inférence (3 jours de prédictions)
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_inference_data(n_days=3, n_samples_per_day=24, feature_columns=None, seed=42):
    """
    Génère des données d'inférence pour n jours
    
    Args:
        n_days: Nombre de jours à prédire (défaut 3)
        n_samples_per_day: Nombre d'échantillons par jour (défaut 24 pour hourly)
        feature_columns: Liste des noms de colonnes features
        seed: Seed pour la reproductibilité
        
    Returns:
        DataFrame avec les données d'inférence et leurs timestamps
    """
    np.random.seed(seed)
    
    # Générer les timestamps
    start_date = datetime.now()
    timestamps = []
    
    for day in range(n_days):
        for hour in range(n_samples_per_day):
            timestamp = start_date + timedelta(days=day, hours=hour)
            timestamps.append(timestamp)
    
    # Utiliser les colonnes par défaut si non spécifiées
    if feature_columns is None:
        feature_columns = ['temperature', 'humidity', 'wind_speed', 'cloud_cover', 
                          'day_of_week', 'hour', 'holiday']
    
    # Générer les features aléatoires
    n_samples = len(timestamps)
    features_data = {}
    
    for col in feature_columns:
        if col == 'temperature':
            features_data[col] = np.random.normal(15, 8, n_samples)  # Moyenne 15, std 8
        elif col == 'humidity':
            features_data[col] = np.random.uniform(30, 90, n_samples)
        elif col == 'wind_speed':
            features_data[col] = np.random.exponential(3, n_samples)
        elif col == 'cloud_cover':
            features_data[col] = np.random.uniform(0, 100, n_samples)
        elif col == 'day_of_week':
            features_data[col] = np.random.randint(0, 7, n_samples)
        elif col == 'hour':
            features_data[col] = np.tile(np.arange(n_samples_per_day), n_days)
        elif col == 'holiday':
            features_data[col] = np.random.randint(0, 2, n_samples)
        else:
            # Features génériques
            features_data[col] = np.random.standard_normal(n_samples)
    
    # Créer le DataFrame
    df_inference = pd.DataFrame(features_data)
    df_inference['timestamp'] = timestamps
    
    logger.info(f"Données d'inférence générées: {df_inference.shape[0]} échantillons sur {n_days} jours")
    logger.info(f"Features: {list(feature_columns)}")
    
    return df_inference


def prepare_features_for_model(df_inference, feature_columns):
    """
    Extrait et prépare les features pour le modèle
    
    Args:
        df_inference: DataFrame d'inférence
        feature_columns: Liste des colonnes features attendues par le modèle
        
    Returns:
        DataFrame contenant uniquement les features, et les timestamps
    """
    try:
        X_inference = df_inference[feature_columns].copy()
        timestamps = df_inference['timestamp'].copy()
        
        logger.info(f"Features préparées: {X_inference.shape}")
        return X_inference, timestamps
        
    except KeyError as e:
        logger.error(f"Colonne manquante: {str(e)}")
        return None, None


def add_predictions_to_data(df_inference, predictions, confidence_scores=None):
    """
    Ajoute les prédictions au DataFrame d'inférence
    
    Args:
        df_inference: DataFrame d'inférence avec timestamps
        predictions: Array de prédictions du modèle
        confidence_scores: Array optionnel de scores de confiance
        
    Returns:
        DataFrame augmenté avec les prédictions
    """
    df_result = df_inference.copy()
    df_result['prediction'] = predictions
    
    if confidence_scores is not None:
        df_result['confidence'] = confidence_scores
    
    logger.info(f"Prédictions ajoutées au DataFrame: {df_result.shape}")
    
    return df_result
