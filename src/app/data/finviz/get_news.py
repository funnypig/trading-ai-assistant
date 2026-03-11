import requests
import pandas as pd

from io import BytesIO
from typing import List

from src.app.data.finviz.utils import with_api_token
from src.app.data.finviz.models import News

NEWS_BASE_URL = 'https://elite.finviz.com/news_export.ashx?'


class FinvizNewsApiParameters:
    market_news_order_time = "v=1&c=1"
    stock_news = "v=3&t=\"{ticker}\""


def get_news_from_url(url: str) -> List[News]:
    response = requests.get(url)
    news_df = pd.read_csv(BytesIO(response.content))
    news = []

    for _, row in news_df.iterrows():
        news.append(News.from_row(row.to_dict()))

    return news


def get_market_news() -> List[News]:
    url = NEWS_BASE_URL + FinvizNewsApiParameters.market_news_order_time
    url = with_api_token(url)
    news = get_news_from_url(url)

    return news


def get_stock_news(ticker: str) -> List[News]:
    url = NEWS_BASE_URL + FinvizNewsApiParameters.stock_news.format(ticker=ticker)
    url = with_api_token(url)
    news = get_news_from_url(url)

    return news


if __name__ == "__main__":
    news = get_stock_news("U")
    print(*news[:5], sep="\n")

    market_news = get_market_news()
    print(*market_news[:5], sep="\n")
