import json
import re
from dataclasses import dataclass
from typing import List, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag
from src.app.data.finviz.utils import get_headers
from src.app.infrastructure.cache.decorator import redis_cache

INCOME_STATEMENT_URL = "https://elite.finviz.com/api/statement.ashx?t={ticker}&so=R&s=IQ"
BALANCE_SHEET_URL = "https://elite.finviz.com/api/statement.ashx?t={ticker}&so=R&s=BQ"
CASH_FLOW_URL = "https://elite.finviz.com/api/statement.ashx?t={ticker}&so=R&s=CQ"
STOCK_DESCRIPTIVE_URL = "https://elite.finviz.com/quote.ashx?t={ticker}&p=d"
_BOXOVER_BODY_RE = re.compile(r"(?<![A-Za-z0-9_])body=\[([^\]]+)\]", re.DOTALL)

FinancialMetric = Tuple[str, str]
OwnershipEntry = Tuple[str, str]


@dataclass
class StockDescriptiveInfo:
    """Structured summary of a stock's description, metrics, and owners."""

    description: str
    financials: List[FinancialMetric]
    institutional_ownership: List[OwnershipEntry]

    def to_markdown(self) -> str:
        """Convert the descriptive info into a simple Markdown string."""

        sections: List[str] = []

        if self.description:
            sections.append("Company description\n" + self.description)

        if self.financials:
            lines = ["Financials"]
            lines.extend(f"- {label}: {value}" for label, value in self.financials)
            sections.append("\n".join(lines))

        if self.institutional_ownership:
            lines = ["Institutional Ownership"]
            lines.extend(f"- {name} {percentage}" for name, percentage in self.institutional_ownership)
            sections.append("\n".join(lines))

        return "\n\n".join(sections).strip()

    def __str__(self):
        return self.to_markdown()


def _descriptive_dumps(info: StockDescriptiveInfo) -> str:
    return json.dumps({
        "description": info.description,
        "financials": info.financials,
        "institutional_ownership": info.institutional_ownership,
    })


def _descriptive_loads(s: str) -> StockDescriptiveInfo:
    data = json.loads(s)
    return StockDescriptiveInfo(
        description=data["description"],
        financials=[tuple(pair) for pair in data["financials"]],
        institutional_ownership=[tuple(pair) for pair in data["institutional_ownership"]],
    )


# API related functions

@redis_cache(ttl=86400, dumps=json.dumps, loads=json.loads)
def get_income_statement(ticker: str) -> dict:
    url = INCOME_STATEMENT_URL.format(ticker=ticker)
    response = requests.get(url, headers=get_headers())

    data = response.json()["data"]
    return data


@redis_cache(ttl=86400, dumps=json.dumps, loads=json.loads)
def get_balance_sheet(ticker: str) -> dict:
    url = BALANCE_SHEET_URL.format(ticker=ticker)
    response = requests.get(url, headers=get_headers())

    data = response.json()["data"]
    return data


@redis_cache(ttl=86400, dumps=json.dumps, loads=json.loads)
def get_cash_flow(ticker: str) -> dict:
    url = CASH_FLOW_URL.format(ticker=ticker)
    response = requests.get(url, headers=get_headers())

    data = response.json()["data"]
    return data


# Aggregation and formatting functions

def data_as_table(data: dict) -> str:
    df = pd.DataFrame.from_dict(data)
    table = df.to_csv(index=False)

    return table


def get_fundamental_info(ticker: str) -> str:
    income_statement = get_income_statement(ticker)
    balance_sheet = get_balance_sheet(ticker)
    cash_flow = get_cash_flow(ticker)

    info = f"""
    ### Income statement

    {data_as_table(income_statement)}

    ### Balance sheet

    {data_as_table(balance_sheet)}

    ### Cash Flow

    {data_as_table(cash_flow)}
    """.strip()

    return info


@redis_cache(ttl=3600, dumps=_descriptive_dumps, loads=_descriptive_loads)
def get_stock_descriptive(ticker: str) -> StockDescriptiveInfo:
    url = STOCK_DESCRIPTIVE_URL.format(ticker=ticker)
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    description = _extract_company_description(soup)
    financials = _extract_snapshot_metrics(soup)
    ownership = _extract_institutional_ownership(soup)

    return StockDescriptiveInfo(
        description=description,
        financials=financials,
        institutional_ownership=ownership,
    )


def _extract_company_description(soup: BeautifulSoup) -> str:
    bio = soup.select_one(".quote_profile-bio")
    if bio:
        return bio.get_text(" ", strip=True)

    fallback = soup.select_one("td.fullview-profile.quote_profile")
    return fallback.get_text(" ", strip=True) if fallback else ""


def _extract_snapshot_metrics(soup: BeautifulSoup) -> List[FinancialMetric]:
    table = soup.select_one("table.snapshot-table2")
    if not table:
        return []

    metrics: List[FinancialMetric] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        for i in range(0, len(cells) - 1, 2):
            label_cell = cells[i]
            value_cell = cells[i + 1]
            label = _parse_metric_label(label_cell)
            value = value_cell.get_text(" ", strip=True)
            if label and value:
                metrics.append((label, value))
    return metrics


def _parse_metric_label(cell: Tag) -> str:
    boxover = cell.get("data-boxover", "")
    match = _BOXOVER_BODY_RE.search(boxover)
    if match:
        tooltip = match.group(1)
        parsed = BeautifulSoup(tooltip, "html.parser").get_text(" ", strip=True)
        if parsed:
            return parsed

    return cell.get_text(" ", strip=True)


def _extract_institutional_ownership(soup: BeautifulSoup) -> List[OwnershipEntry]:
    table_body = soup.select_one(".managers-and-funds table tbody")
    if not table_body:
        return _extract_institutional_ownership_from_script(soup)

    ownership: List[OwnershipEntry] = []
    for row in table_body.find_all("tr"):
        columns = row.find_all("td")
        if len(columns) < 2:
            continue

        name = columns[0].get_text(" ", strip=True)
        percentage = columns[1].get_text(" ", strip=True)
        if name and percentage:
            ownership.append((name, percentage))
    return ownership or _extract_institutional_ownership_from_script(soup)


def _extract_institutional_ownership_from_script(soup: BeautifulSoup) -> List[OwnershipEntry]:
    script = soup.find("script", id="institutional-ownership-init-data-0")
    if not script or not script.string:
        return []

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    ownership: List[OwnershipEntry] = []
    for key in ("managersOwnership", "fundsOwnership"):
        for entry in data.get(key, []):
            name = entry.get("name")
            perc = entry.get("percOwnership")
            if not name or perc is None:
                continue

            ownership.append((name.strip(), f"{perc:.2f}%"))

    return ownership


if __name__ == "__main__":
    #print(get_fundamental_info("MSFT"))
    print(get_stock_descriptive("U"))
