"""
Flow Prefect — Mise à jour hebdomadaire du Feature Store Jenedai
Séquence : enedis_conso → meteo → vacances

Lancement manuel :
    uv run python flow_feature_store.py

Déploiement avec schedule :
    uv run python flow_feature_store.py --deploy
"""

import argparse
import subprocess
import yaml
import sqlalchemy
from datetime import date, timedelta
from pathlib import Path

from prefect import flow, task, get_run_logger


# ── Config ─────────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).parents[3] / "jenedai" / "data" / "connectors"
CONFIG      = SCRIPTS_DIR / "config.yaml"
PROFILE     = "local"
MAX_RECORDS = 40_000

# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_engine(config: Path, profile: str) -> sqlalchemy.Engine:
    """Construit un engine SQLAlchemy depuis config.yaml — même logique que query_table.py."""
    with open(config) as f:
        cfg = yaml.safe_load(f)
    db_cfg = cfg["database"]
    db = db_cfg[profile] if profile in db_cfg else db_cfg
    pwd = db.get("password") or ""
    auth = f"{db['user']}:{pwd}@" if pwd else f"{db['user']}@"
    sslmode = db.get("sslmode", "disable")
    url = (
        f"postgresql+psycopg2://{auth}{db['host']}:{db['port']}/{db['name']}"
        f"?sslmode={sslmode}"
    )
    return sqlalchemy.create_engine(url, pool_pre_ping=True)


def _run(script: str, extra_args: list[str]) -> None:
    """Lance un script via uv run et streame les logs."""
    logger = get_run_logger()
    cmd = [
        "uv", "run", "python",
        str(SCRIPTS_DIR / script),
        "--config", str(CONFIG),
        "--profile", PROFILE,
        *extra_args,
    ]
    logger.info(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{script} a échoué (code {result.returncode})")


# ── Tasks ──────────────────────────────────────────────────────────────────────

@task(name="extract-enedis", retries=2, retry_delay_seconds=60)
def extract_enedis(date_end: str) -> None:
    """Calcule date_start depuis MAX(horodate) en base, puis lance l'extraction."""
    logger = get_run_logger()
    # Récupère la dernière horodate
    engine = _build_engine(CONFIG, PROFILE)
    with engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT MAX(horodate) FROM enedis_conso")
        ).scalar()

    if result is None:
        date_start = (date.today() - timedelta(days=7)).isoformat()
        logger.warning(f"Table vide — fallback date_start = {date_start}")
    else:
        date_start = result.date().isoformat()
        logger.info(f"Dernière horodatage en base : {date_start}")

    if date_start >= date_end:
        logger.info(f"Rien à extraire — base déjà à jour ({date_start} >= {date_end})")
        return

    logger.info(f"Enedis : {date_start} → {date_end} (max {MAX_RECORDS:,} lignes)")
    _run("extract_enedis_to_feature_store.py", [
        "--date-start", date_start,
        "--date-end",   date_end,
        "--max-records", str(MAX_RECORDS),
    ])


@task(name="extract-meteo", retries=2, retry_delay_seconds=60)
def extract_meteo() -> None:
    """Dates auto-détectées depuis enedis_conso."""
    logger = get_run_logger()
    logger.info("Météo : dates auto depuis enedis_conso")
    _run("extract_meteo_to_feature_store.py", [])


@task(name="extract-vacances", retries=2, retry_delay_seconds=60)
def extract_vacances() -> None:
    """Dates auto-détectées depuis enedis_conso."""
    logger = get_run_logger()
    logger.info("Vacances : dates auto depuis enedis_conso")
    _run("extract_vacances_to_feature_store.py", [])


# ── Flow ───────────────────────────────────────────────────────────────────────

@flow(
    name="feature-store-daweekly-update",
    description="Mise à jour hebdomadaire : enedis → météo → vacances",
)
def feature_store_update() -> None:
    
    logger = get_run_logger()

    # logger scripts
    from jenedai.ml.utils.logs import configure_logging
    from jenedai.ml.utils.get_console import get_console
    logs_folder = Path(__file__).parents[4] / "logs"

    # Hors système de logging
    console = get_console()

    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]🔍 Energy predictor Enedis Database updating [/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]\n")
    
    # ✅ Système de logging
    logger_file = configure_logging(
        path_logs=logs_folder,
        name="Datababse_update_enedis.log",
        profile="basic",
    )
    logger_file.info("Système de logs configuré pour la msie à jour de la databse Enedis.")

    date_end = date.today().isoformat()
    logger.info(f"Date de fin : {date_end}")

    # Séquence stricte : chaque tâche attend la précédente
    extract_enedis(date_end)
    extract_meteo()     # attend que enedis soit à jour pour l'auto-détection
    extract_vacances()  # idem
    msg = "Feature Store mis à jour ✅"
    logger.info(msg)
    logger_file.info(msg)

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true", help="Déployer avec schedule hebdomadaire")
    args = parser.parse_args()

    if args.deploy:
        feature_store_update.serve(
            name="feature-store-weekly",
            cron="0 3 * * 1",          # tous les lundis à 03:00 UTC
            tags=["jenedai", "etl", "feature-store"],
            description="Mise à jour hebdomadaire : enedis → météo → vacances",
            pause_on_shutdown=False,
            limit=1,
        )
    else:
        feature_store_update()