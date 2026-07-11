from collections import Counter
from datetime import datetime

import pandas as pd
from prefect import task


class DataValidator:
    """
    Checks performed (in order):
        1. Schema validation
        2. Numeric ID coercion (non-numeric → NaN)
        3. Drop rows with NaN IDs before further checks
        4. ISO 8601 datetime validation
        5. Missing value check on required columns
    """

    SCHEMA_COLS = frozenset(
        [
            "Horodate",
            "Région",
            "Code région",
            "Profil",
            "Place de puissance souscrite",
            "Secteur activité",
            "Nb points soutirage",
            "Total énergie soutirée",
            "Courbe Moyenne n°1",
        ]  # TODO
    )
    REQUIRED_COLS = ["date_time", "id", "type", "location"]  # TODO

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def check_valid_schema(self, df: pd.DataFrame) -> None:
        """Raise ValueError if columns don't match the expected schema."""
        if Counter(df.columns) != Counter(self.SCHEMA_COLS):
            missing = self.SCHEMA_COLS - set(df.columns)
            extra = set(df.columns) - self.SCHEMA_COLS
            raise ValueError(f"Schema mismatch — missing: {missing or '∅'}, extra: {extra or '∅'}")

    def coerce_numeric_id(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert 'id' to numeric; non-numeric values become NaN.
        Rows with NaN ids are dropped and a warning is logged.
        """
        df = df.copy()
        df["id"] = pd.to_numeric(df["id"], errors="coerce")

        invalid_count = df["id"].isna().sum()
        if invalid_count > 0:
            print(f"[WARNING] {invalid_count} row(s) with non-numeric 'id' dropped.")
            df = df.dropna(subset=["id"])

        return df

    def verify_datetime(self, df: pd.DataFrame) -> None:
        """
        Raise ValueError listing all rows where 'date_time' is not ISO 8601.
        """
        invalid_rows = []
        for idx, value in df["Horodate"].items():
            try:
                datetime.fromisoformat(str(value))
            except (ValueError, TypeError):
                invalid_rows.append((idx, value))

        if invalid_rows:
            details = ", ".join(f"row {i}: {v!r}" for i, v in invalid_rows)
            raise ValueError(f"Invalid ISO 8601 datetime(s) — {details}")

    def check_missing_values(self, df: pd.DataFrame) -> None:
        """Raise ValueError if any required column contains null values."""
        errors = []
        for col in self.REQUIRED_COLS:
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"'{col}' has {null_count} missing value(s)")

        if errors:
            raise ValueError("Missing value check failed:\n  " + "\n  ".join(errors))

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    @task
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all validation checks and return the cleaned DataFrame.

        Steps:
            1. Schema check
            2. Coerce IDs to numeric, drop invalid rows
            3. Datetime format check
            4. Missing value check on required columns

        Raises:
            ValueError: on any failed check.
        """
        self.check_valid_schema(df)
        df = self.coerce_numeric_id(df)
        self.verify_datetime(df)
        self.check_missing_values(df)
        return df
