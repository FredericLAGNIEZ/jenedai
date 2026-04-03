
import pandas as pd
from pathlib import Path


def load(path_file : str) -> pd.DataFrame:
    df = pd.read_csv(
        path_file,
        sep=";",
        dtype=str,
    )
    return df