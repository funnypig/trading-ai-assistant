import requests
import pandas as pd

from io import BytesIO
from enum import Enum

from src.app.data.finviz.client import with_api_token
from src.app.infrastructure.cache.decorator import redis_cache
from src.app.infrastructure.cache.serializers import df_dumps, df_loads

GET_QUOTE_URL = "https://elite.finviz.com/quote_export.ashx?t={ticker}&p={p}&r={r}"


class FinvizQuoteParameters(Enum):
    daily = dict(p="d", r="1y")
    hour_4 = dict(p="h15", r="m6")
    hour_1 = dict(p="h1", r="m1")
    min_15 = dict(p="i15", r="d5")
    min_5 = dict(p="i5", r="d5")


@redis_cache(ttl=900, dumps=df_dumps, loads=df_loads)
def get_stock_quote(ticker: str, period: FinvizQuoteParameters = FinvizQuoteParameters.daily) -> pd.DataFrame:
    url = GET_QUOTE_URL.format(ticker=ticker, **period.value)
    url = with_api_token(url)

    response = requests.get(url)
    df = pd.read_csv(BytesIO(response.content))

    return df
