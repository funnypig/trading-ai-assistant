"""Article content extraction from arbitrary news URLs.

Uses trafilatura as the primary extractor (content-density heuristics) with a
BeautifulSoup fallback targeting semantic HTML containers.
"""

from __future__ import annotations

import requests
import trafilatura
from bs4 import BeautifulSoup

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
REQUEST_TIMEOUT = 15  # seconds
MIN_CONTENT_LENGTH = 200  # characters — below this is likely a paywall stub


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_with_trafilatura(html: str) -> str | None:
    return trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
    )


def extract_with_bs4(html: str) -> str | None:
    """Target semantic content containers, strip boilerplate tags."""
    soup = BeautifulSoup(html, "html5lib")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
        tag.decompose()

    container = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.find(id=lambda v: v and "content" in v.lower())
        or soup.find(class_=lambda v: v and "article" in " ".join(v).lower())
        or soup.body
    )
    if container is None:
        return None

    paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p") if len(p.get_text(strip=True)) > 40]
    return "\n\n".join(paragraphs) or None


def extract_article(url: str) -> str:
    """Fetch and extract clean article text from a URL.

    Returns extracted text, or a bracketed message on failure (paywall, bot
    protection, network error, etc.).
    """
    try:
        html = fetch_html(url)
    except requests.RequestException as exc:
        return f"[Could not fetch URL: {exc}]"

    text = extract_with_trafilatura(html)

    if not text or len(text) < MIN_CONTENT_LENGTH:
        text = extract_with_bs4(html)

    if not text or len(text) < MIN_CONTENT_LENGTH:
        return "[Content not available — likely a paywall, bot protection, or empty page.]"

    return text.strip()
