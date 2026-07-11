import pandas as pd


class Transformer:
    TARGET = "total_energie_soutiree_wh"
    """
    Transformations (in order):
        1. Remove rows with NaN 'id'
        2. Deduplicate on 'id', keeping first occurrence
        3. Split 'date_time' into month, day columns
    """

    def rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns to snake_case."""
        rename_map = {
            "Unnamed: 0": "id",
            # "Horodate": "date"
            # "Région":                                    "region",
            # "Code région":                               "code_region",
            # "Profil":                                    "profil",
            # "Plage de puissance souscrite":              "plage_puissance",
            # "Secteur activité":                          "secteur_activite",
            # "Nb points soutirage":                       "nb_points_soutirage",
            # "Total énergie soutirée (Wh)":               "total_energie_soutiree_wh",
        }

        return df.rename(columns=rename_map)

    def reset_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reset index after drops/filters."""
        return df.reset_index(drop=True)

    def aggregate_date(self, df: pd.DataFrame) -> pd.DataFrame:

        to_keep = [
            "secteur_activite",
            "plage_de_puissance_souscrite",
            "nb_points_soutirage",
            "horodate",
            "region",
            "total_energie_soutiree_wh",
        ]

        df_to_agg = df.loc[:, to_keep].copy()
        df_to_agg["jour"] = pd.to_datetime(df_to_agg["horodate"]).dt.date

        group_cols = ["jour", "secteur_activite", "plage_de_puissance_souscrite", "region"]

        df_daily = (
            df_to_agg.groupby(group_cols)
            .agg(
                nb_points_soutirage=("nb_points_soutirage", "mean"),
                total_energie_soutiree_wh=("total_energie_soutiree_wh", "mean"),
            )
            .reset_index()
        )

        # Préparation df_extra
        extra_cols = [
            "horodate",
            "secteur_activite",
            "plage_de_puissance_souscrite",
            "region",
            "ville",
            "vacances_zone_a",
            "vacances_zone_b",
            "vacances_zone_c",
            "temperature_2m_mean",
            "relative_humidity_mean",
            "precipitation_sum",
        ]
        df_extra = df.loc[:, extra_cols].copy()
        df_extra["jour"] = pd.to_datetime(df_extra["horodate"]).dt.date
        df_extra = df_extra.drop_duplicates(subset=group_cols)
        df_extra = df_extra.drop(columns=["horodate"])

        # Merge
        df_final = df_daily.merge(df_extra, on=group_cols, how="left")

        return df_final

    def split_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrait month et day depuis 'date_time' déjà casté en datetime."""
        df["jour"] = pd.to_datetime(df["jour"], format="ISO8601", errors="coerce")
        dt = df["jour"]  # déjà datetime64 après DataCaster
        df["month"] = dt.dt.month.astype("category")  # Int8 suffisant (1-12)
        df["day"] = dt.dt.day.astype("Int8")  # Int8 suffisant (1-31)
        df["jour_semaine"] = dt.dt.dayofweek.astype("category")
        df = df.drop(["jour"], axis=1)
        df = df.drop(["day"], axis=1)
        return df

    def transform_vacances_features(self, df) -> pd.DataFrame:
        # Fonction pour vérifier si la ville est en vacances dans au moins une zone
        df["en_vacances"] = (
            (df["vacances_zone_a"] == "True")
            | (df["vacances_zone_b"] == "True")
            | (df["vacances_zone_c"] == "True")
        ).astype(int)

        df = df.drop(columns=["vacances_zone_a", "vacances_zone_b", "vacances_zone_c"])
        return df

        # @task

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.rename_columns(df)
        df = self.reset_index(df)
        df = self.aggregate_date(df)
        df = self.split_datetime(df)
        df = self.transform_vacances_features(df)
        df = df.dropna()  # erase all nan..
        return df


# ajouter : arrondi du nb points soutirage,
# ajouter l'aggrégation
