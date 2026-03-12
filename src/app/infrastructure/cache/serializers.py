import json
from io import StringIO

import pandas as pd


def df_dumps(df: pd.DataFrame) -> str:
    return df.to_json(orient="split")


def df_loads(s: str) -> pd.DataFrame:
    return pd.read_json(StringIO(s), orient="split")
