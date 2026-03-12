import requests
import pandas as pd

from io import BytesIO
from pathlib import Path

from src.app.data.finviz.utils import with_api_token
from src.app.tools.options.get_expiration_date import get_nearest_expiration
from src.app.infrastructure.cache.decorator import redis_cache
from src.app.infrastructure.cache.serializers import df_dumps, df_loads

OPTION_CHAIN_URL = 'https://elite.finviz.com/export/options?t={ticker}&ty=oc&e={expiration}'


@redis_cache(ttl=300, dumps=df_dumps, loads=df_loads)
def _fetch_option_chain(ticker: str, expiration: str) -> pd.DataFrame:
    url = with_api_token(OPTION_CHAIN_URL.format(ticker=ticker, expiration=expiration))
    response = requests.get(url)
    return pd.read_csv(BytesIO(response.content))


def get_option_chain(ticker: str, expiration: str | None = None, file_path: Path | None = None) -> pd.DataFrame:
    if expiration is None:
        expiration = get_nearest_expiration()

    option_chain = _fetch_option_chain(ticker, expiration)

    if file_path:
        option_chain.to_csv(file_path)

    return option_chain


if __name__ == "__main__":
    import time

    t1 = time.time()
    chain = get_option_chain("CF")
    t2 = time.time()

    print(f"Chain loaded in {round(t2-t1, 5)} sec")
