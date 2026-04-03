"""
Préparation et prétraitement des données
Inclut: détection auto des types, imputation, scaling, encoding
"""
import pandas as pd
import numpy as np
import logging
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_feature_types(X):
    """
    Détecte automatiquement les colonnes numériques et catégories
    
    Args:
        X: DataFrame avec les features
    
    Returns:
        tuple: (numeric_features, categorical_features)
    """
    numeric_features = []
    categorical_features = []
    
    for col, dtype in X.dtypes.items():
        if ('float' in str(dtype)) or ('int' in str(dtype)):
            numeric_features.append(col)
        else:
            categorical_features.append(col)
    
    logger.info(f"🔍 Features numériques détectées: {numeric_features}")
    logger.info(f"🔍 Features catégories détectées: {categorical_features}")
    
    return numeric_features, categorical_features


def create_preprocessor(numeric_features, categorical_features):
    """
    Crée un preprocessor avec pipelines pour données numériques et catégories
    
    Args:
        numeric_features: Liste des colonnes numériques
        categorical_features: Liste des colonnes catégories
    
    Returns:
        ColumnTransformer: Preprocessor configuré
    """
    # Pipeline pour features numériques
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])
    logger.info("✓ Pipeline numériques créé: Imputer(mean) + Scaler")
    
    # Pipeline pour features catégories
    categorical_transformer = Pipeline(steps=[
        ('encoder', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
    ])
    logger.info("✓ Pipeline catégories créé: OneHotEncoder")
    
    # ColumnTransformer pour combiner les deux
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'  # Ignorer les colonnes non listées
    )
    logger.info("✓ ColumnTransformer créé")
    
    return preprocessor


def get_feature_names(preprocessor, numeric_features, categorical_features):
    """
    Récupère les noms des colonnes après transformation
    
    Args:
        preprocessor: ColumnTransformer configuré et fitted
        numeric_features: Liste des features numériques
        categorical_features: Liste des features catégories
    
    Returns:
        list: Noms des colonnes transformées
    """
    feature_names = []
    
    # Features numériques (inchangées)
    feature_names.extend(numeric_features)
    
    # Features catégories (encodées)
    if categorical_features:
        try:
            encoder = preprocessor.named_steps['cat'].named_steps['encoder']
            cat_names = encoder.get_feature_names_out(categorical_features)
            feature_names.extend(cat_names)
        except Exception as e:
            logger.warning(f"Impossible de récupérer les noms de features catégories: {e}")
    
    return feature_names


def prepare_data(X_train, X_test, numeric_features=None, categorical_features=None):
    """
    Prépare les données: détection auto des types, création et application du preprocessor
    
    Args:
        X_train: Features d'entraînement
        X_test: Features de test
        numeric_features: Optionnel, liste des features numériques (auto-détection si None)
        categorical_features: Optionnel, liste des features catégories (auto-détection si None)
    
    Returns:
        dict: Contenant X_train_transformed, X_test_transformed, preprocessor, feature_names
    """
    logger.info("=== PRÉPARATION DES DONNÉES ===")
 
    # Détection automatique si non fourni
    if numeric_features is None or categorical_features is None:
        logger.info("\n1️⃣ Détection des types de features...")
        num_features, cat_features = detect_feature_types(X_train)
        if numeric_features is None:
            numeric_features = num_features
        if categorical_features is None:
            categorical_features = cat_features
    
    # Créer le preprocessor
    logger.info("\n2️⃣ Création du preprocessor...")
    preprocessor = create_preprocessor(numeric_features, categorical_features)
    
    # Appliquer sur train set
    logger.info("\n3️⃣ Transformation du training set...")
    X_train_transformed = preprocessor.fit_transform(X_train)
    logger.info(f"  ✓ Shape: {X_train_transformed.shape}")
    
    # Appliquer sur test set
    logger.info("\n4️⃣ Transformation du test set...")
    X_test_transformed = preprocessor.transform(X_test)
    logger.info(f"  ✓ Shape: {X_test_transformed.shape}")
    
    # Récupérer les noms des features
    logger.info("\n5️⃣ Récupération des noms de features...")
    feature_names = get_feature_names(preprocessor, numeric_features, categorical_features)
    logger.info(f"  ✓ {len(feature_names)} features au total")
    
    result = {
        'X_train': X_train_transformed,
        'X_test': X_test_transformed,
        'preprocessor': preprocessor,
        'feature_names': feature_names,
        'numeric_features': numeric_features,
        'categorical_features': categorical_features
    }
    
    logger.info("\n✓ Préparation des données terminée\n")
    return result


def transform_new_data(X_new, preprocessor):
    """
    Transforme de nouvelles données avec un preprocessor déjà configuré
    
    Args:
        X_new: Nouvelles données à transformer
        preprocessor: ColumnTransformer déjà fitted
    
    Returns:
        array: Données transformées
    """
    X_new_transformed = preprocessor.transform(X_new)
    logger.info(f"✓ Nouvelles données transformées: {X_new_transformed.shape}")
    return X_new_transformed
