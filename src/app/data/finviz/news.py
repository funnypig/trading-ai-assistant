import json
import requests
import pandas as pd

from io import BytesIO
from typing import List

from src.app.data.finviz.client import with_api_token
from src.app.domain.models import News
from src.app.infrastructure.cache.decorator import redis_cache

NEWS_BASE_URL = 'https://elite.finviz.com/news_export.ashx?'


class FinvizNewsApiParameters:
    market_news_order_time = "v=1&c=1"
    stock_news = "v=3&t=\"{ticker}\""


def _news_dumps(news: List[News]) -> str:
    return json.dumps([{"title": n.title, "date": n.date, "url": n.url, "ticker": n.ticker} for n in news])


def _news_loads(s: str) -> List[News]:
    return [News(**d) for d in json.loads(s)]


def get_news_from_url(url: str) -> List[News]:
    response = requests.get(url)
    news_df = pd.read_csv(BytesIO(response.content))
    news = []

    for _, row in news_df.iterrows():
        news.append(News.from_row(row.to_dict()))

    return news


@redis_cache(ttl=300, dumps=_news_dumps, loads=_news_loads)
def get_market_news() -> List[News]:
    url = NEWS_BASE_URL + FinvizNewsApiParameters.market_news_order_time
    url = with_api_token(url)
    news = get_news_from_url(url)

    return news


@redis_cache(ttl=300, dumps=_news_dumps, loads=_news_loads)
def get_stock_news(ticker: str) -> List[News]:
    url = NEWS_BASE_URL + FinvizNewsApiParameters.stock_news.format(ticker=ticker)
    url = with_api_token(url)
    news = get_news_from_url(url)

    return news


if __name__ == "__main__":
    import time

    t1 = time.time()
    news = get_stock_news("U")
    t2 = time.time()
    print(*news[:5], sep="\n")
    print(f"Got stock news in {round(t2 - t1, 5)} sec")

    t1 = time.time()
    market_news = get_market_news()
    t2 = time.time()
    print(*market_news[:5], sep="\n")
    print(f"Got market news in {round(t2 - t1, 5)} sec")
