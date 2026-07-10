from datetime import datetime
import pandas as pd
from prefect import task


class DataCaster:
    """
    Casts DataFrame columns to specified types.

    Casts performed (in order):
        1. Numeric columns  → float or int (non-castable → NaN)
        2. String columns   → str (NaN preserved)
        3. Datetime columns → datetime64 (non-castable → NaT)
        4. Boolean columns  → bool (non-castable → NaN via nullable BooleanDtype)
        5. Category columns → category
    """

    NUMERIC_COLS: list[str] = [
        "Code région",
        "Nb points soutirage",
        "Total énergie soutirée",
        "Courbe Moyenne n°1",
    ]
    STRING_COLS: list[str] = [
        "Région",
        "Profil",
        "Place de puissance souscrite",
        "Secteur activité",
    ]
    DATETIME_COLS: list[str] = ["Horodate"]
    BOOLEAN_COLS: list[str] = []   # TODO
    CATEGORY_COLS: list[str] = []  # TODO

    # ------------------------------------------------------------------
    # Individual casters
    # ------------------------------------------------------------------

    def cast_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Coerce numeric columns to float; non-castable values become NaN."""
        df = df.copy()
        for col in self.NUMERIC_COLS:
            if col not in df.columns:
                continue
            before = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            after = df[col].isna().sum()
            new_nulls = after - before
            if new_nulls > 0:
                print(f"[WARNING] '{col}': {new_nulls} value(s) could not be cast to numeric → NaN.")
        return df

    def cast_string(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast string columns to str; existing NaN/None are preserved as pd.NA."""
        df = df.copy()
        for col in self.STRING_COLS:
            if col not in df.columns:
                continue
            df[col] = df[col].where(df[col].isna(), df[col].astype("category"))

        return df

    def cast_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse datetime columns with ISO 8601 format.
        Non-parseable values become NaT and a warning is logged.
        """
        df = df.copy()
        for col in self.DATETIME_COLS:
            if col not in df.columns:
                continue
            before = df[col].isna().sum()
            df[col] = pd.to_datetime(df[col], format="ISO8601", errors="coerce")
            after = df[col].isna().sum()
            new_nulls = after - before
            if new_nulls > 0:
                print(f"[WARNING] '{col}': {new_nulls} value(s) could not be parsed as datetime → NaT.")
        return df

    def cast_boolean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cast boolean columns to pandas nullable BooleanDtype.
        Non-castable values become pd.NA.
        """
        df = df.copy()
        for col in self.BOOLEAN_COLS:
            if col not in df.columns:
                continue
            try:
                df[col] = df[col].astype("boolean")
            except (ValueError, TypeError) as e:
                print(f"[WARNING] '{col}': could not be cast to boolean → skipped. ({e})")
        return df

    def cast_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast category columns to pandas CategoricalDtype."""
        df = df.copy()
        for col in self.CATEGORY_COLS:
            if col not in df.columns:
                continue
            df[col] = df[col].astype("category")
        return df

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    @task
    def cast(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all casting steps and return the typed DataFrame.

        Steps:
            1. Numeric columns  → float64  (errors → NaN)
            2. String columns   → str      (NaN preserved)
            3. Datetime columns → datetime64[ns] (errors → NaT)
            4. Boolean columns  → BooleanDtype   (errors → pd.NA)
            5. Category columns → category

        Returns:
            pd.DataFrame: DataFrame with columns cast to their target types.
        """
        df = self.cast_numeric(df)
        df = self.cast_string(df)
        df = self.cast_datetime(df)
        df = self.cast_boolean(df)
        df = self.cast_category(df)
        return df