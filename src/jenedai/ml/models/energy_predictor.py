import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib


class EnergyPredictor:
    """
    Encapsule le pipeline :
      - préprocessing (scaling + encoding)
      - entraînement RandomForest
      - prédiction sur nouvelles données (réelles ou synthétiques)
    """
   
    TARGET = "total_energie_soutiree_wh"

    FEATURES = [
    "secteur_activite", "plage_de_puissance_souscrite", "nb_points_soutirage",
    "ville", "en_vacances", "temperature_2m_mean", "relative_humidity_mean",
    "precipitation_sum", "month", "jour_semaine"
]
    SECTEURS = ["S1: Agriculture", "S2: Industrie", "S3: Tertiaire", "S4: Non Affecté"]

    PLAGES_PUISSANCE = [
        "P1: ]36-120] kVA", "P2: ]120-250] kVA", "P3: Total ]36-250] kVA",
        "P4: ]250-1000] kVA", "P5: ]1000-2000] kVA", "P6: > 2000 kVA",
        "P7: Total > 250 kVA"
    ]

    VILLES = ["Paris", "Lyon", "Marseille", "Toulouse", "Nantes", "Lille", "Orléans", "Rouen", "Dijon" ,"Rennes"]

    MOIS = [str(i) for i in range(1, 13)]
    JOURS = [str(i) for i in range(7)]
    VACANCES = ["0", "1"]


    def __init__(self, n_estimators=100, max_depth=10, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state

        self.preprocessor = None
        self.model = None

        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1
        )
    # ── Construction du preprocessor ──────────────────────────────────────────

    def _validate_features(self, df: pd.DataFrame) -> None:
        missing = set(self.FEATURES) - set(df.columns)
        if missing:
            raise ValueError(
                f"Colonnes manquantes : {sorted(missing)}\n"
                f"Attendues : {self.FEATURES}"
            )

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
    

    def _build_pipeline(self, X: pd.DataFrame, n_estimators: int, max_depth: int) -> Pipeline:
        numeric_features = [c for c, t in X.dtypes.items() if 'float' in str(t) or 'int' in str(t)]
        categorical_features = [c for c, t in X.dtypes.items() if c not in numeric_features]

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('encoder', OneHotEncoder(drop='first', handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

        return Pipeline(
            steps=[
                ("Preprocessing", preprocessor),
                ("Classifier", self.model
                ),
            ],
            verbose=True,
        )

    # ── Entraînement ──────────────────────────────────────────────────────────

    # def fit(self, df: pd.DataFrame, test_size: float = 0.2):
    #     """
    #     Entraîne le modèle à partir du DataFrame brut.
    #     Retourne les métriques sur le jeu de test.
    #     """
    #     self._validate_features(df)

    #     X = df[self.FEATURES]
    #     Y = df[self.TARGET]
    #     X_train, X_test, Y_train, Y_test = train_test_split(
    #         X, Y, test_size=test_size, random_state=self.random_state
    #     )
    #     # Mémoriser les catégories réelles
    #     self.categories_ = {
    #         col: X_train[col].dropna().unique().tolist()
    #         for col in X_train.select_dtypes(include='object').columns
    #     }
    #     self.numeric_stats_ = X_train.describe()

    #     self.preprocessor = self._build_preprocessor(X_train)
    #     X_train_t = self.preprocessor.fit_transform(X_train)
    #     X_test_t  = self.preprocessor.transform(X_test)

    #     self.model.fit(X_train_t, Y_train)

    #     Y_pred = self.model.predict(X_test_t)
    #     mae = mean_absolute_error(Y_test, Y_pred)
    #     r2  = r2_score(Y_test, Y_pred)

    #     print(f"✅ Modèle entraîné — MAE : {mae:.2f} | R² : {r2:.4f}")
    #     return {"mae": mae, "r2": r2}

    def fit(self, df: pd.DataFrame, test_size: float = 0.2):
        self._validate_features(df)

        X = df[self.FEATURES]
        Y = df[self.TARGET]
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=test_size, random_state=self.random_state
        )

        self.categories_ = {
            col: X_train[col].dropna().unique().tolist()
            for col in X_train.select_dtypes(include='object').columns
        }
        self.numeric_stats_ = X_train.describe()

        self.pipeline = self._build_pipeline(X_train, self.n_estimators, self.max_depth)
        self.pipeline.fit(X_train, Y_train)

        Y_pred = self.pipeline.predict(X_test)
        mae = mean_absolute_error(Y_test, Y_pred)
        r2  = r2_score(Y_test, Y_pred)
        results = {"mae": mae, "r2": r2}
        print(f"✅ Modèle entraîné — MAE : {mae:.2f} | R² : {r2:.4f}")

        return X_train, Y_pred, results

             
    # ── Prédiction ────────────────────────────────────────────────────────────
    def predict(self, sample: dict) -> float:
        """
        Prédit l'énergie soutirée pour un exemple (dict).
        """
        if self.model is None:
            raise RuntimeError("Modèle non entraîné. Appelez fit() d'abord.")

        sample_df = pd.DataFrame([sample])[self.FEATURES]
        self._validate_features(sample_df)

        # Conversion bool → int AVANT le transform
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
        return {
            "secteur_activite": np.random.choice(self.SECTEURS),
            "plage_de_puissance_souscrite": np.random.choice(self.PLAGES_PUISSANCE),
            "nb_points_soutirage":  float(np.random.uniform(0, 1500)),
            "ville": np.random.choice(self.VILLES),
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

     # ── Save ────────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Sérialise preprocessor + modèle + métadonnées."""
        if self.model is None:
            raise RuntimeError("Rien à sauvegarder : modèle non entraîné.")
        
        joblib.dump({
            "preprocessor": self.preprocessor,
            "model":        self.model,
            "categories_":  self.categories_,
            "params": {
                "n_estimators": self.n_estimators,
                "max_depth":    self.max_depth,
                "random_state": self.random_state,
            }
        }, path)

    @classmethod
    def load(cls, path: str) -> "EnergyPredictor":
        """Recharge un modèle sauvegardé sans ré-entraîner."""
        data = joblib.load(path)
        params = data["params"]
        instance = cls(**params)
        instance.preprocessor  = data["preprocessor"]
        instance.model         = data["model"]
        instance.categories_   = data["categories_"]
        return instance