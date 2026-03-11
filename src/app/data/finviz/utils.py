from src.app.config.config import settings


def with_api_token(url: str) -> str:
    return f'{url}&auth={settings.finviz_api_key}'


def get_headers() -> dict:
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    }
