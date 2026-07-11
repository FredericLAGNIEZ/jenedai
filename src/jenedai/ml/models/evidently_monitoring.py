import smtplib
import warnings
from email.message import EmailMessage

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.metrics import ValueDrift

# Imports légers
from prefect import get_run_logger, task


## MONITORING DATA
@task(name="monitor", retries=1, retry_delay_seconds=30, tags=["monitor"])
def monitor_task(reference: pd.DataFrame, production: pd.DataFrame) -> pd.DataFrame | None:
    """Surveillance des données de production par rapport aux données de référence"""
    # Ignore only RuntimeWarnings
    warnings.simplefilter("ignore", RuntimeWarning)

    logger = get_run_logger()

    try:
        parsed_reference = Dataset.from_pandas(reference, data_definition=DataDefinition())
        parsed_production = Dataset.from_pandas(production, data_definition=DataDefinition())

        # report = Report([DataDriftPreset()])
        # data_stability = report.run(current_data=parsed_production, reference_data=parsed_reference)

        # data_drift_dict = data_stability.dict()

        COLUMNS_TO_MONITOR = ["total_energie_soutiree_wh", "nb_points_soutirage"]

        report = Report(metrics=[ValueDrift(column=col) for col in COLUMNS_TO_MONITOR])

        data_stability = report.run(current_data=parsed_production, reference_data=parsed_reference)

        data_drift_dict = data_stability.dict()

        drift_summary = check_drift(data_drift_dict, logger=logger)

        if drift_summary["has_drift"]:
            columns_list = ", ".join(r["column"] for r in drift_summary["drifted_columns"])
            logger.warning(f"⚠️ Drift détecté sur : {columns_list}")

            msg = EmailMessage()
            msg["From"] = "test@example.com"
            msg["To"] = "destinataire@example.com"
            msg["Subject"] = (
                f"Alerte! Drift détecté sur {len(drift_summary['drifted_columns'])} colonne(s)"
            )

            body_lines = ["Colonnes en drift :\n"]
            for r in drift_summary["drifted_columns"]:
                body_lines.append(f"- {r['column']}: {r['value']:.4f} (seuil {r['threshold']})")
            msg.set_content("\n".join(body_lines))

            with smtplib.SMTP("localhost", 8025) as smtp:
                smtp.send_message(msg)
        else:
            logger.info("✅ Aucun drift significatif détecté.")

        return data_drift_dict

    except Exception as e:
        msg = "Loading error on Monitor Data Pipeline"
        logger.error(f" {msg} : {e}")
        return None


def check_drift(data_drift_dict: dict, logger=None) -> dict:
    """
    Parcourt toutes les métriques ValueDrift du rapport Evidently
    et retourne un résumé des colonnes en drift.
    """
    drifted_columns = []
    all_results = []

    for metric in data_drift_dict.get("metrics", []):
        config = metric.get("config", {})
        column = config.get("column")
        threshold = config.get("threshold")
        value = metric.get("value")

        # On ne traite que les métriques de type ValueDrift (ignore les autres types de metrics)
        if column is None or threshold is None or value is None:
            continue

        is_drifted = float(value) > float(threshold)

        result = {
            "column": column,
            "value": float(value),
            "threshold": float(threshold),
            "drifted": is_drifted,
        }
        all_results.append(result)

        if is_drifted:
            drifted_columns.append(result)

        if logger:
            status = "🔴 DRIFT" if is_drifted else "🟢 OK"
            logger.info(f"{status} — {column}: {value:.4f} (seuil {threshold})")

    return {
        "drifted_columns": drifted_columns,
        "all_results": all_results,
        "has_drift": len(drifted_columns) > 0,
    }
