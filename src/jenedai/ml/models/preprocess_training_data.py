"""
Prétraitement de la vue v_training_data exportée en CSV.
Normalise les types pour correspondre au format cible Jenedai.

Usage :
    uv run preprocess_training_data.py --input exports/v_training_data.csv
    uv run preprocess_training_data.py --input exports/v_training_data.csv --output exports/v_training_data_clean.csv
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Schéma attendu ─────────────────────────────────────────────────────────────

BOOL_COLS = [
    "zone_a", "zone_b", "zone_c",
    "vacances_zone_a", "vacances_zone_b", "vacances_zone_c",
]

DATETIME_COLS = ["horodate"]
DATE_COLS     = ["date"]

NUMERIC_COLS = [
    "total_energie_soutiree_wh",
    "nb_points_soutirage",
    "lat", "lon",
    "temperature_2m_mean",
    "relative_humidity_mean",
    "precipitation_sum",
    "jour_max_du_mois_0_1",
    "semaine_max_du_mois_0_1",
]

CATEGORICAL_COLS = [
    "secteur_activite",
    "plage_de_puissance_souscrite",
    "region",
    "ville",
    "nom_vacances",
    "profil",
]

# ── Parsing args ───────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Prétraitement v_training_data")
    parser.add_argument(
        "--input", required=True,
        help="Chemin vers le CSV brut exporté depuis PostgreSQL",
    )
    parser.add_argument(
        "--output", default=None,
        help="Chemin de sortie (défaut : même dossier que l'input, suffixe _clean)",
    )
    return parser.parse_args()


# ── Chargement ─────────────────────────────────────────────────────────────────

def load_csv(path: str) -> pd.DataFrame:
    """Détecte automatiquement le séparateur et le decimal."""
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    # Détection séparateur : virgule ou tabulation
    with open(filepath, encoding="utf-8") as f:
        first_line = f.readline()
    sep = "\t" if first_line.count("\t") > first_line.count(",") else ","

    # Détection decimal : virgule ou point
    decimal = "," if sep == "," and ";" not in first_line else "."

    df = pd.read_csv(filepath, sep=sep, decimal=decimal, low_memory=False)
    logger.info(f"Chargé : {len(df):,} lignes × {len(df.columns)} colonnes (sep='{sep}', decimal='{decimal}')")
    return df


# ── Nettoyage ──────────────────────────────────────────────────────────────────

def normalize_booleans(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise t/f, True/False, 0/1 → bool Python."""
    bool_map = {
        "t": True, "f": False,
        "true": True, "false": False,
        "1": True, "0": False,
        True: True, False: False,
        1: True, 0: False,
    }
    for col in BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].map(
                lambda x: bool_map.get(str(x).strip().lower(), None)
                if pd.notna(x) else None
            )
    return df


def normalize_datetimes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise horodate → YYYY-MM-DDTHH:MM:SSZ (UTC)."""
    for col in DATETIME_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
            df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise date → YYYY-MM-DD."""
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def normalize_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Force les colonnes numériques en float/int."""
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def normalize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace sur les colonnes texte."""
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("nan", None)
    return df


def report(df: pd.DataFrame) -> None:
    """Affiche un résumé du DataFrame nettoyé."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Shape final : {df.shape}")
    logger.info(f"Nulls par colonne :")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    for col, n in nulls.items():
        logger.info(f"  {col:<35} {n:>6} nulls ({100*n/len(df):.1f}%)")
    logger.info(f"{'='*60}")


# ── Pipeline ───────────────────────────────────────────────────────────────────

def preprocess(input_path: str, output_path: str | None) -> pd.DataFrame:
    df = load_csv(input_path)

    df = normalize_booleans(df)
    df = normalize_datetimes(df)
    df = normalize_dates(df)
    df = normalize_numerics(df)
    df = normalize_categoricals(df)

    report(df)

    # Résolution chemin de sortie
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_clean{p.suffix}")

    df.to_csv(output_path, index=False, sep=",", decimal=".", encoding="utf-8")
    logger.info(f"Export OK → {output_path}")

    return df


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    preprocess(args.input, args.output)


if __name__ == "__main__":
    main() 
