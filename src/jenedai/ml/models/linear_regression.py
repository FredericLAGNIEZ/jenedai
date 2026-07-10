
import numpy as np
 
 
class LinearRegression:
    """
    Régression linéaire simple utilisant la méthode des moindres carrés ordinaires (OLS).
    Modèle : y = X @ w + b
    """
 
    def __init__(self):
        self.weights = None  # coefficients (pentes)
        self.bias = None     # intercept
 
    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearRegression":
        """
        Entraîne le modèle sur les données (X, y).
 
        Paramètres
        ----------
        X : array de forme (n_samples, n_features)
        y : array de forme (n_samples,)
 
        Retourne
        --------
        self
        """
        X = np.array(X)
        y = np.array(y)
 
        n_samples = X.shape[0]
 
        # Ajoute une colonne de 1 pour le biais (intercept)
        X_b = np.c_[np.ones(n_samples), X]  # forme : (n_samples, n_features + 1)
 
        # Solution analytique : θ = (X^T X)^{-1} X^T y
        theta = np.linalg.pinv(X_b.T @ X_b) @ X_b.T @ y
 
        self.bias = theta[0]
        self.weights = theta[1:]
 
        return self
 
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les valeurs pour X.
 
        Paramètres
        ----------
        X : array de forme (n_samples, n_features)
 
        Retourne
        --------
        y_pred : array de forme (n_samples,)
        """
        if self.weights is None:
            raise RuntimeError("Le modèle n'est pas encore entraîné. Appelez fit() d'abord.")
 
        return np.array(X) @ self.weights + self.bias
 

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Calcule le coefficient de détermination R².
 
        Paramètres
        ----------
        X : array de forme (n_samples, n_features)
        y : array de forme (n_samples,)
 
        Retourne
        --------
        r2 : float entre -∞ et 1 (1 = prédiction parfaite)
        """
        y = np.array(y)
        y_pred = self.predict(X)
 
        ss_res = np.sum((y - y_pred) ** 2)       # somme des carrés des résidus
        ss_tot = np.sum((y - y.mean()) ** 2)      # somme totale des carrés
 
        return 1 - ss_res / ss_tot
 
    def __repr__(self) -> str:
        if self.weights is None:
            return "LinearRegression(non entraîné)"
        return f"LinearRegression(weights={self.weights}, bias={self.bias:.4f})"
 