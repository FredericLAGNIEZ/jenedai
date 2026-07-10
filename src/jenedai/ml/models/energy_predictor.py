import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


class EnergyPredictor:
    """
    Encapsule le pipeline :
      - préprocessing (scaling + encoding)
      - entraînement RandomForest
      - prédiction sur nouvelles données (réelles ou synthétiques)
    """

    FEATURES = [
        "secteur_activite", "plage_de_puissance_souscrite", "nb_points_soutirage",
        "ville", "en_vacances",  # ← une seule colonne 0 ou 1
        "temperature_2m_mean", "relative_humidity_mean", "precipitation_sum",
        "month", "jour_semaine"
    ]

    
    TARGET = "total_energie_soutiree_wh"

    def __init__(self, n_estimators=100, max_depth=10, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state

        self.preprocessor = None
        self.model = None

    # ── Construction du preprocessor ──────────────────────────────────────────

    def _build_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        numeric_features = [c for c, t in X.dtypes.items() if 'float' in str(t) or 'int' in str(t)]
        categorical_features = [c for c, t in X.dtypes.items() if c not in numeric_features]

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
        ('encoder', OneHotEncoder(drop='first', handle_unknown='ignore'))  # ← ajout
        ])

        return ColumnTransformer(transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    # ── Entraînement ──────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame, test_size: float = 0.2):
        """
        Entraîne le modèle à partir du DataFrame brut.
        Retourne les métriques sur le jeu de test.
        """
        X = df[self.FEATURES]
        Y = df[self.TARGET]

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=test_size, random_state=self.random_state
        )

        self.preprocessor = self._build_preprocessor(X_train)
        X_train_t = self.preprocessor.fit_transform(X_train)
        X_test_t  = self.preprocessor.transform(X_test)

        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.model.fit(X_train_t, Y_train)

        Y_pred = self.model.predict(X_test_t)
        mae = mean_absolute_error(Y_test, Y_pred)
        r2  = r2_score(Y_test, Y_pred)

        print(f"✅ Modèle entraîné — MAE : {mae:.2f} | R² : {r2:.4f}")
        return {"mae": mae, "r2": r2}

    # ── Prédiction ────────────────────────────────────────────────────────────

    def predict(self, sample: dict) -> float:
        """
        Prédit l'énergie soutirée pour un exemple (dict ou DataFrame 1 ligne).

        """
        if self.model is None:
            raise RuntimeError("Modèle non entraîné. Appelez fit() d'abord.")

        sample_df = pd.DataFrame([sample])[self.FEATURES]
        sample_t  = self.preprocessor.transform(sample_df)

        for col in sample_df.select_dtypes(include='bool').columns:
            sample_df[col] = sample_df[col].astype(int)

        sample_t = self.preprocessor.transform(sample_df)
        return float(self.model.predict(sample_t)[0])

    
    def predict_random_sample(self, df_raw: pd.DataFrame = None) -> dict:
        """
        Génère un échantillon aléatoire synthétique et prédit l'énergie soutirée.
        df_raw est gardé en paramètre pour compatibilité mais n'est plus utilisé.
        """
        if self.model is None:
            raise RuntimeError("Modèle non entraîné. Appelez fit() d'abord.")

        sample = self._generate_random_sample()
        sample_df = pd.DataFrame([sample])[self.FEATURES]
        sample_t = self.preprocessor.transform(sample_df)
        predicted = float(self.model.predict(sample_t)[0])

        print(f"🤖 Valeur prédite : {predicted:,.0f} Wh")
        print(f"📋 Échantillon    : {sample}")

        return {"predicted": predicted, "sample": sample}

   
    def _generate_random_sample(self) -> dict:
        """
        Génère un dict aléatoire dans le format exact attendu par le modèle.
        Valeurs catégorielles basées sur les données réelles d'entraînement.
        """
        import numpy as np
        return {
            "secteur_activite": np.random.choice([
                "S1: Agriculture", "S2: Industrie", "S3: Tertiaire",
                "S4: Résidentiel", "S5: Eclairage public"
            ]),
            "plage_de_puissance_souscrite": np.random.choice([
                "P1: ]36-120] kVA", "P2: ]120-250] kVA", "P3: ]250-500] kVA",
                "P4: ]500-1000] kVA", "P5: ]1000-2000] kVA"
            ]),
            "nb_points_soutirage":    float(np.random.uniform(0, 1500)),
            "ville": np.random.choice([
                "Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse",
                "Nantes", "Strasbourg", "Rennes", "Dijon", "Lille"
            ]),
            "en_vacances":            int(np.random.randint(0, 2)),
            "temperature_2m_mean":    float(np.random.uniform(-5, 35)),
            "relative_humidity_mean": float(np.random.uniform(55, 95)),
            "precipitation_sum":      float(np.random.uniform(0, 20)),
            "month":                  int(np.random.randint(1, 13)),
            "jour_semaine":           int(np.random.randint(0, 7)),
        }

    def __repr__(self):
        status = "entraîné" if self.model else "non entraîné"
        return f"EnergyPredictor(n_estimators={self.n_estimators}, max_depth={self.max_depth}) [{status}]"

