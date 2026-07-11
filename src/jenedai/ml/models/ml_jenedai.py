import numpy as np
import pandas as pd
from prefect import task
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class MLPipeline:
    TARGET = "total_energie_soutiree_wh"
    TEST_SIZE = 0.2
    RANDOM_STATE = 0

    def __init__(self):
        self.preprocessor: ColumnTransformer | None = None
        self.regressor: LinearRegression | None = None
        self.numeric_features: list[str] = []
        self.categorical_features: list[str] = []

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _detect_features(self, X: pd.DataFrame) -> None:
        """Automatically detect numeric and categorical column names."""
        self.numeric_features = []
        self.categorical_features = []
        for col, dtype in X.dtypes.items():
            if ("float" in str(dtype)) or ("int" in str(dtype)):
                self.numeric_features.append(col)
            else:
                self.categorical_features.append(col)
        print("Found numeric features    :", self.numeric_features)
        print("Found categorical features:", self.categorical_features)

    def _build_preprocessor(self) -> ColumnTransformer:
        """Build the ColumnTransformer from detected feature lists."""
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
            ]
        )
        categorical_transformer = Pipeline(
            steps=[
                ("encoder", OneHotEncoder(drop="first", handle_unknown="ignore")),
            ]
        )
        return ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, self.numeric_features),
                ("cat", categorical_transformer, self.categorical_features),
            ]
        )

    # ------------------------------------------------------------------ #
    #  Tasks                                                               #
    # ------------------------------------------------------------------ #

    @task
    def split_data(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split dataset into train / test sets."""
        print("Dividing into train and test sets...")
        X = df.drop(columns=[self.TARGET])
        Y = df[self.TARGET]
        X_train, X_test, Y_train, Y_test = train_test_split(
            X,
            Y,
            test_size=self.TEST_SIZE,
            random_state=self.RANDOM_STATE,
        )
        print(f"  Train: {X_train.shape}  |  Test: {X_test.shape}")
        print("...Done.\n")
        return X_train, X_test, Y_train, Y_test

    @task
    def ml_transform(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Detect features, build and fit the preprocessor on the train set,
        then apply it to both sets.
        NOTE: preprocessor is *only* fitted on X_train to avoid data leakage.
        """
        self._detect_features(X_train)
        self.preprocessor = self._build_preprocessor()

        print("Performing preprocessings on train set...")
        X_train_t = self.preprocessor.fit_transform(X_train)
        print("...Done.")
        print(X_train_t[:5])
        print()

        print("Performing preprocessings on test set...")
        X_test_t = self.preprocessor.transform(X_test)  # transform only — no fit!
        print("...Done.")
        print(X_test_t[:5])
        print()

        return X_train_t, X_test_t

    @task
    def train_model(
        self,
        X_train: np.ndarray,
        Y_train: pd.Series,
    ) -> LinearRegression:
        """Fit a LinearRegression on the training set."""
        print("Training model...")
        self.regressor = LinearRegression()
        self.regressor.fit(X_train, Y_train)
        print("...Done.\n")
        return self.regressor

    @task
    def evaluate_model(
        self,
        X_test: np.ndarray,
        Y_test: pd.Series,
    ) -> dict[str, float]:
        """Evaluate the model on the test set and log metrics."""
        if self.regressor is None:
            raise RuntimeError("Model not trained yet — call train_model() first.")

        print("Evaluating model on test set...")
        Y_pred = self.regressor.predict(X_test)

        metrics = {
            "r2": round(r2_score(Y_test, Y_pred), 4),
            "mae": round(mean_absolute_error(Y_test, Y_pred), 4),
            "rmse": round(np.sqrt(mean_squared_error(Y_test, Y_pred)), 4),
        }

        print(f"  R²   : {metrics['r2']}")
        print(f"  MAE  : {metrics['mae']}")
        print(f"  RMSE : {metrics['rmse']}")
        print("...Done.\n")
        return metrics

    @task
    def save_model(self, path: str = "model.joblib") -> None:
        """Persist the trained model and preprocessor to disk."""
        import joblib

        if self.regressor is None or self.preprocessor is None:
            raise RuntimeError("Nothing to save — pipeline not fully trained.")

        payload = {
            "regressor": self.regressor,
            "preprocessor": self.preprocessor,
        }
        joblib.dump(payload, path)
        print(f"Model saved → {path}\n")

        # # Automatically detect names of numeric/categorical columns


# numeric_features = []
# categorical_features = []
# for i,t in X.dtypes.items():
#     if ('float' in str(t)) or ('int' in str(t)) :
#         numeric_features.append(i)
#     else :
#         categorical_features.append(i)

# print('Found numeric features ', numeric_features)
# print('Found categorical features ', categorical_features)

# # Divide dataset Train set & Test set
# print("Dividing into train and test sets...")
# X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)
# print("...Done.")
# print()


# # Create pipeline for numeric features
# numeric_transformer = Pipeline(steps=[
#     ('imputer', SimpleImputer(strategy='mean')), # missing values will be replaced by columns' mean
#     ('scaler', StandardScaler())
# ])

# # Create pipeline for categorical features
# categorical_transformer = Pipeline(
#     steps=[
#     ('encoder', OneHotEncoder(drop='first')) # first column will be dropped to avoid creating correlations between features
#     ])


# # Use ColumnTransformer to make a preprocessor object that describes all the treatments to be done
# preprocessor = ColumnTransformer(
#     transformers=[
#         ('num', numeric_transformer, numeric_features),
#         ('cat', categorical_transformer, categorical_features)
#     ])

#     # Preprocessings on train set
# print("Performing preprocessings on train set...")
# print(X_train.head())
# X_train = preprocessor.fit_transform(X_train)
# print('...Done.')
# print(X_train[0:5]) # MUST use this syntax because X_train is a numpy array and not a pandas DataFrame anymore
# print()

# # Preprocessings on test set
# print("Performing preprocessings on test set...")
# print(X_test.head())
# X_test = preprocessor.transform(X_test) # Don't fit again !! The test set is used for validating decisions
# # we made based on the training set, therefore we can only apply transformations that were parametered using the training set.
# # Otherwise this creates what is called a leak from the test set which will introduce a bias in all your results.
# print('...Done.')
# print(X_test[0:5,:]) # MUST use this syntax because X_test is a numpy array and not a pandas DataFrame anymore
# print()


# # Train model
# print("Train model...")
# regressor = LinearRegression()
# regressor.fit(X_train, Y_train)
# print("...Done.")
