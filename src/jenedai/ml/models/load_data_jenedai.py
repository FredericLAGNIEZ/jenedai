
import pandas as pd
# from pathlib import Path


# CSV
def load_data_csv(logger, path_file : str) -> pd.DataFrame:
    try:
        df = pd.read_csv(
        path_file,
        sep=";",
        dtype=str,
    )
    except Exception as e :
        logger.error(e)
    return df


from sqlalchemy import create_engine
import pandas as pd

PG_URL = "postgresql+psycopg2://enedis:enedis_secret@localhost:5434/feature_store"

def load_data(logger) -> pd.DataFrame:
    try:
        engine = create_engine(PG_URL)
        df = pd.read_sql("SELECT * FROM v_training_data", engine)
        logger.info(f"{len(df)} lignes chargées depuis le Feature Store")
        return df
    except Exception as e:
        logger.error(e)
        raise