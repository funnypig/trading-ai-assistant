import requests
import pandas as pd

from io import BytesIO

from src.app.data.finviz.client import with_api_token
from src.app.infrastructure.cache.decorator import redis_cache
from src.app.infrastructure.cache.serializers import df_dumps, df_loads


@redis_cache(ttl=900, dumps=df_dumps, loads=df_loads)
def get_screener_by_url(url: str) -> pd.DataFrame:
    url = with_api_token(url)

    response = requests.get(url)
    df = pd.read_csv(BytesIO(response.content))

    return df


def get_hourly_oversold_screener() -> pd.DataFrame:
    url = "https://elite.finviz.com/screener.ashx?" \
        "v=111&f=cap_midover,fa_curratio_o1,fa_epsyoy1_o5,fa_pe_profitable," \
        "geo_usa,sh_opt_optionshort,ta_rsi_os40,tad_0_rsi:14:rsi:h|blweq:::|value:::30&ft=3&o=-marketcap"
    return get_screener_by_url(url)


def get_daily_oversold_screener() -> pd.DataFrame:
    url = "https://elite.finviz.com/screener.ashx?" \
        "v=111&f=cap_midover,fa_curratio_o1,fa_epsyoy1_o5,fa_pe_profitable,geo_usa,sh_opt_optionshort,ta_rsi_os30&ft=3&o=-marketcap"
    return get_screener_by_url(url)


def get_high_short_float_screener() -> pd.DataFrame:
    url = "https://elite.finviz.com/screener.ashx?" \
        "v=151&f=cap_midover,geo_usa,ipodate_more5,sh_float_o1,sh_opt_short,sh_price_o5,sh_short_o10&o=-shortinterestshare"
    return get_screener_by_url(url)
