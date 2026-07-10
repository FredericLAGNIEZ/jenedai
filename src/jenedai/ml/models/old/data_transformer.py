import pandas as pd
from prefect import task


class CambridgePoliceDataTransformer:
    """
    Applies cleaning and structural transformations to a Cambridge Police
    incident DataFrame.

    Transformations (in order):
        1. Remove rows with NaN 'id' (non-numeric IDs flagged upstream)
        2. Deduplicate on 'id', keeping first occurrence
        3. Split 'date_time' into year, month, day, hour, minute, second columns
    """

    # ------------------------------------------------------------------
    # Individual transformations
     # ------------------------------------------------------------------
    def rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns to snake_case."""
        rename_map = {
            "Unnamed: 0" : "id"
            # "Horodate":                                  "horodate",
            # "Région":                                    "region",
            # "Code région":                               "code_region",
            # "Profil":                                    "profil",
            # "Plage de puissance souscrite":              "plage_puissance",
            # "Secteur activité":                          "secteur_activite",
            # "Nb points soutirage":                       "nb_points_soutirage",
            # "Total énergie soutirée (Wh)":               "total_energie_soutiree_wh",
            # "Courbe Moyenne n°1 (Wh)":                   "courbe_moyenne_1_wh",
            # "Indice représentativité Courbe n°1 (%)":    "indice_repres_1_pct",
            # "Courbe Moyenne n°2 (Wh)":                   "courbe_moyenne_2_wh",
            # "Indice représentativité Courbe n°2 (%)":    "indice_repres_2_pct",
            # "Courbe Moyenne n°1 + n°2 (Wh)":             "courbe_moyenne_1_2_wh",
            # "Indice représentativité Courbe n°1 + n°2 (%)": "indice_repres_1_2_pct",
            # "Jour max du mois (0/1)":                    "jour_max_mois",
            # "Semaine max du mois (0/1)":                 "semaine_max_mois",

        }
        return df.rename(columns=rename_map)

    def reset_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reset index after drops/filters."""
        return df.reset_index(drop=True)
        
    def remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Drop rows where 'id' is NaN.
        These were coerced to NaN upstream during numeric validation.

        Must run before deduplication: NaN != NaN, so duplicated NaN ids
        would survive drop_duplicates incorrectly.
        """
        before = len(df)
        df = df.dropna(subset=["id"])
        dropped = before - len(df)
        if dropped:
            print(f"[INFO] remove_invalid_rows: {dropped} row(s) removed.")
        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate rows based on 'id', keeping the first occurrence.
        """
        before = len(df)
        df = df.drop_duplicates(subset=["id"], keep="first")
        dropped = before - len(df)
        if dropped:
            print(f"[INFO] remove_duplicates: {dropped} duplicate(s) removed.")
        return df

    def split_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse 'date_time' and extract year, month, day, hour, minute, second
        into separate columns.

        The original 'date_time' string column is preserved.
        A parsed '_date_time' intermediate column is used then dropped.
        """
        df = df.copy()
        parsed = pd.to_datetime(df["date_time"])

        df["year"] = parsed.dt.year
        df["month"] = parsed.dt.month
        df["day"] = parsed.dt.day
        df["hour"] = parsed.dt.hour
        df["minute"] = parsed.dt.minute
        df["second"] = parsed.dt.second

        return df

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    @task
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all transformations and return the cleaned DataFrame.

        Steps (order matters):
            1. Drop invalid rows (NaN ids) — must precede deduplication
            2. Deduplicate on 'id'
            3. Split 'date_time' into component columns

        Returns:
            Transformed pd.DataFrame with additional time columns.
        """
        df = self.remove_invalid_rows(df)
        df = self.remove_duplicates(df)
        df = self.split_datetime(df)
        return df
