
import pandas as pd
from pathlib import Path


# CSV
def load_data(logger, path_file : str) -> pd.DataFrame:
    try:
        df = pd.read_csv(
        path_file,
        sep=";",
        dtype=str,
    )
    except Exception as e :
        logger.error(e)
    return df