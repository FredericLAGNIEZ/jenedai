"""
Chargement et préparation des données
"""
import pandas as pd
import yaml
from pathlib import Path


def load_config(config_path="utils/config.yaml"):
    """Charge la configuration depuis le fichier YAML"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_data(file_path):
    """Charge les données depuis un fichier CSV"""
    try:
        data = pd.read_csv(file_path, sep=";", lineterminator="\n", encoding="utf-8")
        print(f"Données chargées avec succès: {file_path}")
        print(f"Forme des données: {data.shape}")
        print(f"Colonnes: {list(data.columns)}")
        print(f"Types: {data.dtypes.to_dict()}")
        print(f"Head: {data.head(5)}")
        
        # Vérifier les données
        if data.empty:
            print("Attention: Le fichier est vide")
        if data.isnull().sum().sum() > 0:
            print(f"Attention: {data.isnull().sum().sum()} valeurs manquantes détectées")
        
        return data
    except FileNotFoundError:
        print(f"Erreur: Fichier non trouvé - {file_path}")
        return None
    except Exception as e:
        print(f"Erreur lors du chargement: {e}")
        return None


def split_data(data, test_size=0.2, random_state=42):
    """
    Divise les données en ensemble d'entraînement et de test
    Nettoie aussi les données (NaN, types)
    """
    from sklearn.model_selection import train_test_split
    
    if data is None or data.empty:
        raise ValueError("Les données sont vides ou None")
    
    # Nettoyer les données
    data_clean = data.dropna()  # Supprimer les NaN
    if data_clean.empty:
        raise ValueError("Toutes les données contiennent des NaN")
    
    print(f"Données après nettoyage: {data_clean.shape}")
    
    # Séparer features et target (dernière colonne)
    X = data_clean.iloc[:, :-1]
    y = data_clean.iloc[:, -1]
    print(f"Features shape: {X.shape}, Target shape: {y.shape}")

    y = y.astype(str).str.strip()
    y = pd.to_numeric(y, errors='coerce')

    mask = y.notna()
    X = X[mask]
    y = y[mask]
    
    # Vérifier que X et y ne sont pas vides
    if X.empty or y.empty:
        raise ValueError(f"X ou y vide après split: X.shape={X.shape}, y.shape={y.shape}")
    
    # Convertir en types numériques si possible
    try:
        X = X.astype(float)
        y = pd.to_numeric(y, errors='coerce').dropna()
        # Re-aligner X et y après conversion
        X = X.loc[y.index]
    except Exception as e:
        print(f"Attention: Conversion numérique partiellement échouée: {e}")
    
    if X.empty:
        raise ValueError("X est vide après conversion")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size,
        random_state=random_state,
        stratify=None  # Pas de stratification si y est continu
    )
    
    print(f"Ensemble d'entraînement: {X_train.shape}")
    print(f"Ensemble de test: {X_test.shape}")
    
    return X_train, X_test, y_train, y_test


def save_data(data, file_path):
    """Sauvegarde les données dans un fichier CSV"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(file_path, index=False)
    print(f"Données sauvegardées: {file_path}")
