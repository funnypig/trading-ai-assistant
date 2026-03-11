import requests
import pandas as pd

from io import BytesIO
from pathlib import Path

from src.app.data.finviz.utils import with_api_token
from src.app.tools.options.get_expiration_date import get_nearest_expiration

OPTION_CHAIN_URL = 'https://elite.finviz.com/export/options?t={ticker}&ty=oc&e={expiration}'


def get_option_chain(ticker: str, expiration: str | None = None, file_path: Path | None = None) -> pd.DataFrame:
    if expiration is None:
        expiration = get_nearest_expiration()
    
    url = with_api_token(OPTION_CHAIN_URL.format(ticker=ticker, expiration=expiration))
    response = requests.get(url)

    option_chain = pd.read_csv(BytesIO(response.content))

    if file_path:
        option_chain.to_csv(file_path)

    return option_chain
