from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from jenedai.ml.scripts.train_flow import load_task_bdd

MODULE = "jenedai.ml.scripts.train_flow"
PREPROCESS = "jenedai.ml.models.preprocess_training_data"


@pytest.fixture
def fake_config(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(
        "database:\n local:\n  user: u\n  password: p\n  host: h\n  port: 5432\n  name: db\n"
    )
    return str(p)


@patch(f"{MODULE}.get_run_logger", return_value=MagicMock())
def test_success(_, fake_config):
    with (
        patch("sqlalchemy.create_engine") as mock_engine,
        patch("pandas.read_sql_query") as mock_read_sql,
        patch(f"{PREPROCESS}.normalize_booleans", side_effect=lambda df: df),
        patch(f"{PREPROCESS}.normalize_datetimes", side_effect=lambda df: df),
        patch(f"{PREPROCESS}.normalize_dates", side_effect=lambda df: df),
        patch(f"{PREPROCESS}.normalize_numerics", side_effect=lambda df: df),
        patch(f"{PREPROCESS}.normalize_categoricals", side_effect=lambda df: df),
        patch(f"{PREPROCESS}.report"),
    ):
        mock_read_sql.return_value = pd.DataFrame({"a": [1, 2]})
        mock_engine.return_value.connect.return_value.__enter__.return_value = MagicMock()

        result = load_task_bdd.fn(fake_config, profile="local")

    assert len(result) == 2


@patch(f"{MODULE}.get_run_logger", return_value=MagicMock())
def test_config_invalide(_):
    assert load_task_bdd.fn("inexistant.yaml", profile="local") is None


@patch(f"{MODULE}.get_run_logger", return_value=MagicMock())
def test_df_vide(_, fake_config):
    with (
        patch("sqlalchemy.create_engine") as mock_engine,
        patch("pandas.read_sql_query") as mock_read_sql,
    ):
        mock_read_sql.return_value = pd.DataFrame()
        mock_engine.return_value.connect.return_value.__enter__.return_value = MagicMock()
        assert load_task_bdd.fn(fake_config, profile="local") is None


@patch(f"{MODULE}.get_run_logger", return_value=MagicMock())
def test_erreur_requete(_, fake_config):
    with patch("sqlalchemy.create_engine") as mock_engine:
        mock_engine.return_value.connect.side_effect = Exception("boom")
        assert load_task_bdd.fn(fake_config, profile="local") is None
