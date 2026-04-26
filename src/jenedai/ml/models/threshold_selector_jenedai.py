

"""
Variance Threshold Feature Selector

Automatically removes features with low or zero variance that provide
little information for prediction.
"""

import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from typing import Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')


class VarianceThresholdSelector:
    """
    Removes low-variance features using configurable thresholds.
    Handles continuous and binary features appropriately.
    """
    
    def __init__(self, threshold: float = 0.01, normalize: bool = True):
        """
        Initialize the variance threshold selector.
        
        Parameters:
        -----------
        threshold : float
            Variance threshold below which features are removed (default: 0.01)
        normalize : bool
            Whether to normalize variance by feature range (default: True)
        """
        self.threshold = threshold
        self.normalize = normalize
        self.selected_features_ = None
        self.removed_features_ = None
        self.feature_variances_ = None

    def fit(self, X: pd.DataFrame, feature_names: List[str] = None) -> 'VarianceThresholdSelector':

        if isinstance(X, pd.DataFrame):
            if feature_names is not None:
                X = X[feature_names]
            
            X_numeric = X.select_dtypes(include=[np.number])
            print(f"DEBUG colonnes numériques : {X_numeric.columns.tolist()}")  # 👈
            print(f"DEBUG shape : {X_numeric.shape}")                            # 👈
            
            if X_numeric.shape[1] != X.shape[1]:
                dropped = set(X.columns) - set(X_numeric.columns)
                print(f"⚠️  Colonnes non-numériques ignorées : {dropped}")
            
            feature_names = X_numeric.columns.tolist()
            X_array = X_numeric.values.astype(float)
        else:
            X_array = np.array(X, dtype=float)
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(X_array.shape[1])]

        variances = np.var(X_array, axis=0)
        print(f"DEBUG variances : {variances}")  # 👈

        if self.normalize:
            ranges = np.ptp(X_array, axis=0)
            ranges[ranges == 0] = 1
            normalized_variances = variances / (ranges ** 2)
        else:
            normalized_variances = variances

        mask = normalized_variances > self.threshold
        print(f"DEBUG mask : {mask}")  # 👈

        self.selected_features_ = [f for f, m in zip(feature_names, mask) if m]
        self.removed_features_ = [f for f, m in zip(feature_names, mask) if not m]
        self.feature_variances_ = dict(zip(feature_names, normalized_variances))
        
        print(f"DEBUG selected : {self.selected_features_}")  # 👈

        return self
        
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.selected_features_ is None:
            raise ValueError("Selector has not been fitted yet. Call fit() first.")
        
        if isinstance(X, pd.DataFrame):
            # ✅ On ne garde que les selected_features_ qui existent dans X
            available = [f for f in self.selected_features_ if f in X.columns]
            missing = set(self.selected_features_) - set(available)
            if missing:
                print(f"⚠️  Features absentes du DataFrame : {missing}")
            return X[available]
        else:
            # ✅ Fix : X est un array, pas un DataFrame — X.columns n'existe pas
            if self.selected_features_ is None:
                raise ValueError("Impossible de transformer un array sans fit préalable.")
            indices = list(range(len(self.selected_features_)))  # fallback positionnel
            return X[:, indices]


    def fit_transform(self, X: pd.DataFrame, feature_names: List[str] = None) -> pd.DataFrame:
        self.fit(X, feature_names)
        
        # ✅ transform doit recevoir le même sous-ensemble que fit
        if isinstance(X, pd.DataFrame) and feature_names is not None:
            return self.transform(X[feature_names].select_dtypes(include=[np.number]))
        return self.transform(X)


    def get_report(self) -> pd.DataFrame:
        if self.feature_variances_ is None:
            raise ValueError("Selector has not been fitted yet. Call fit() first.")
        
        report_data = [
            {
                'Feature': feature,
                'Variance': variance,
                'Selected': feature in self.selected_features_,
                'Status': 'Kept' if feature in self.selected_features_ else 'Removed'
            }
            for feature, variance in self.feature_variances_.items()
        ]
        
        df = pd.DataFrame(report_data)
        return df.sort_values('Variance', ascending=False).reset_index(drop=True)

        

def demo_variance_selector():
    """Demonstrate variance threshold selector usage."""
    
    # Create sample dataset
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'constant_feature': [1] * n_samples,  # Zero variance
        'low_variance': np.random.normal(10, 0.1, n_samples),  # Very low variance
        'binary_feature': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),  # Imbalanced binary
        'normal_feature': np.random.normal(0, 1, n_samples),  # Normal variance
        'high_variance': np.random.normal(0, 10, n_samples),  # High variance
    }
    
    df = pd.DataFrame(data)
    
    print("=" * 60)
    print("Variance Threshold Feature Selection Demo")
    print("=" * 60)
    
    # Initialize and fit selector
    selector = VarianceThresholdSelector(threshold=0.01, normalize=True)
    selector.fit(df)
    
    # Display report
    print("\nFeature Variance Report:")
    print("-" * 60)
    report = selector.get_report()
    print(report.to_string(index=False))
    
    print(f"\nSelected Features: {len(selector.selected_features_)}")
    print(f"Removed Features: {len(selector.removed_features_)}")
    
    # Transform data
    df_selected = selector.transform(df)
    print(f"\nOriginal shape: {df.shape}")
    print(f"Selected shape: {df_selected.shape}")
    print(f"\nRemaining features: {df_selected.columns.tolist()}")


if __name__ == "__main__":
    demo_variance_selector()
  