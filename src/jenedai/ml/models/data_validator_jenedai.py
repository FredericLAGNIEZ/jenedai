from collections import Counter

import pandas as pd


class DataValidator:
    """
    Valide la structure et le contenu d'un DataFrame selon des règles prédéfinies.
    Les vérifications sont effectuées dans l'ordre suivant :
        1. Validation du schéma (colonnes attendues)
        2. Validation du format ISO 8601 pour la colonne "Horodate"
        3. Vérification des valeurs manquantes dans les colonnes requises

    Attributs :
        SCHEMA_COLS (frozenset) : Ensemble des colonnes attendues dans le DataFrame.
        REQUIRED_COLS (list) : Liste des colonnes pour lesquelles les valeurs manquantes ne sont pas autorisées.

    Méthodes :
        check_valid_schema(df) : Vérifie que le DataFrame respecte le schéma attendu.
        verify_datetime(df) : Vérifie que la colonne "Horodate" contient des dates valides au format ISO 8601.
        check_missing_values(df) : Vérifie l'absence de valeurs manquantes dans les colonnes requises.
        validate(df) : Exécute toutes les validations et retourne le DataFrame si tout est valide.
    """

    SCHEMA_COLS = frozenset(
        [
            "secteur_activite",
            "jour_max_du_mois_0_1",
            "horodate",
            "semaine_max_du_mois_0_1",
            "plage_de_puissance_souscrite",
            "region",
            "total_energie_soutiree_wh",
            "nb_points_soutirage",
            "date",
            "ville",
            "lat",
            "lon",
            "zone_a",
            "zone_b",
            "zone_c",
            "vacances_zone_a",
            "vacances_zone_b",
            "vacances_zone_c",
            "nom_vacances",
            "temperature_2m_mean",
            "relative_humidity_mean",
            "precipitation_sum",
        ]
    )

    REQUIRED_COLS = [
        "secteur_activite",
        "plage_de_puissance_souscrite",
        "total_energie_soutiree_wh",
        "nb_points_soutirage",
        "horodate",
        "ville",
        "region",
        "vacances_zone_a",
        "vacances_zone_b",
        "vacances_zone_c",
        "temperature_2m_mean",
        "relative_humidity_mean",
        "precipitation_sum",
    ]

    # REMOVED :  'lat', 'lon' utilisés pour la météo,  'semaine_max_du_mois_0_1' : données incomplètes

    TARGET = "total_energie_soutiree_wh"
    COL_DATE = "horodate"

    # COLUMNS SCHEMA
    def check_valid_schema(self, df: pd.DataFrame) -> None:
        if Counter(df.columns) != Counter(self.SCHEMA_COLS):
            missing = self.SCHEMA_COLS - set(df.columns)
            extra = set(df.columns) - self.SCHEMA_COLS
            raise ValueError(f"Schema mismatch — missing: {missing or '∅'}, extra: {extra or '∅'}")

    def remove_non_used_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_to_keep = [col for col in self.REQUIRED_COLS if col in df.columns]
        return df[cols_to_keep]

    # CAST DATETIME
    def verify_datetime(self, df: pd.DataFrame) -> None:
        parsed = pd.to_datetime(df[self.COL_DATE], format="ISO8601", errors="coerce")
        invalid_mask = parsed.isna() & df[self.COL_DATE].notna()

        if invalid_mask.any():
            invalid_rows = df.loc[invalid_mask, self.COL_DATE]
            details = ", ".join(f"row {i}: {v!r}" for i, v in invalid_rows.items())
            raise ValueError(f"Invalid ISO 8601 datetime(s) — {details}")

    # DUPLICATES
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """ """
        before = len(df)
        df = df.drop_duplicates(keep="first")
        dropped = before - len(df)
        if dropped:
            print(f"[INFO] remove_duplicates: {dropped} duplicate(s) removed.")
        return df

    def check_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Vérifie la présence de doublons dans le DataFrame et les affiche.
        Ne supprime rien.
        """
        n_duplicates = df.duplicated().sum()

        if n_duplicates > 0:
            print(f"[WARNING] {n_duplicates} doublon(s) détecté(s).")
            print(df[df.duplicated(keep=False)])
        else:
            print("[INFO] Aucun doublon détecté.")

        return df

    # MISSING VALUES
    def remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.dropna(
            subset=[
                self.TARGET,
                "ville",
                "temperature_2m_mean",
                "relative_humidity_mean",
                "precipitation_sum",
            ]
        )  # pas de inplace, pas de copy
        dropped = before - len(df)
        if dropped:
            print(f"[INFO] remove_invalid_rows: {dropped} row(s) removed.")
        return df

    def check_missing_values(self, df: pd.DataFrame) -> None:
        existing_cols = [col for col in self.REQUIRED_COLS if col in df.columns]
        null_counts = df[existing_cols].isna().sum()
        errors = [
            f"'{col}' has {count} missing value(s)"
            for col, count in null_counts.items()
            if count > 0
        ]

        if errors:
            raise ValueError("Missing value check failed:\n  " + "\n  ".join(errors))

    # @task
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        self.check_valid_schema(df)
        df = self.remove_non_used_columns(df)
        self.verify_datetime(df)
        df = self.remove_invalid_rows(df)
        self.check_missing_values(df)
        return df
