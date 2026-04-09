# Backward-compatibility shim — use data/finviz/news.py instead.
from src.app.data.finviz.news import (
    get_stock_news,
    get_market_news,
    get_news_from_url,
)
from src.app.domain.models import News

__all__ = ["get_stock_news", "get_market_news", "get_news_from_url", "News"]
