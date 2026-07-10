

import pandas as pd
from prefect import task

class DataCaster:
    """
    Casts performed (in order):
        1. Datetime columns → datetime64
        2. Numeric columns  → Int64 or float64 (non-castable → NaN)
        3. String columns   → str (NaN preserved)
        4. Boolean columns  → bool (0/1 integers)
    """


    SCHEMA_COLS = frozenset(['secteur_activite',
        'jour_max_du_mois_0_1',
        'horodate',
        'semaine_max_du_mois_0_1',
        'plage_de_puissance_souscrite',
        'region',
        'total_energie_soutiree_wh',
        'nb_points_soutirage',
        'date',
        'ville',
        'lat',
        'lon',
        'zone_a',
        'zone_b',
        'zone_c',
        'vacances_zone_a',
        'vacances_zone_b',
        'vacances_zone_c',
        'nom_vacances',
        'temperature_2m_mean',
        'relative_humidity_mean',
        'precipitation_sum'
    ])

    DATETIME_COLS: list[str] = [
        'horodate',
    ]
    NUMERIC_COLS: list[str] = [
        "nb_points_soutirage",
        "total_energie_soutiree_wh",
        'temperature_2m_mean',
        'relative_humidity_mean',
        'precipitation_sum'   
    ]
    

    STRING_COLS: list[str] = [
        "region",
        'ville'
        "profil",
        'plage_de_puissance_souscrite',
        'secteur_activite',
    ]

    def cast_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in self.DATETIME_COLS:
            if col not in df.columns:
                continue                
            before = df[col].isna().sum()
            df[col] = pd.to_datetime(df[col], format="ISO8601", errors="coerce")
            new_nulls = df[col].isna().sum() - before
            if new_nulls > 0:
                print(f"[WARNING] '{col}': {new_nulls} value(s) could not be parsed as datetime → NaT.")
        return df

    def cast_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in self.NUMERIC_COLS:
            if col not in df.columns:
                continue
            before = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            new_nulls = df[col].isna().sum() - before
            if new_nulls > 0:
                print(f"[WARNING] '{col}': {new_nulls} value(s) could not be cast to numeric → NaN.")
        return df

    def cast_string(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.STRING_COLS:
            if col not in df.columns:
                continue
            df[col] = df[col].astype("category").where(df[col].notna(), other=pd.NA)
        return df

    def cast_boolean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast 0/1 integer columns to pandas nullable BooleanDtype."""
        df = df.copy()
        for col in self.BOOLEAN_COLS:
            if col not in df.columns:
                continue
            try:
                df[col] = df[col].astype("boolean")
            except (ValueError, TypeError) as e:
                print(f"[WARNING] '{col}': could not be cast to boolean → skipped. ({e})")
        return df

    #@task
    def cast(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Steps:
            1. datetime64[ns, UTC] — Horodate
            2. Int64 / float64     — colonnes numériques
            3. str                 — colonnes texte
            4. BooleanDtype        — Jour/Semaine max du mois
        """
        df = self.cast_datetime(df)
        df = self.cast_numeric(df)
        df = self.cast_string(df)
        # df = self.cast_boolean(df)
        return df