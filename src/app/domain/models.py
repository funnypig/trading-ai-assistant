"""Domain value objects shared across data providers and services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Tuple

FinancialMetric = Tuple[str, str]
OwnershipEntry = Tuple[str, str]


class FromRowMixin:
    @classmethod
    def from_row(cls, row):
        row = {k.lower(): v for k, v in row.items()}
        return cls(**{
            f.lower(): row[f]
            for f in cls.__dataclass_fields__
            if f.lower() in row
        })


@dataclass
class News(FromRowMixin):
    title: str
    date: str
    url: str
    ticker: str = ''  # missing for general market news


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

    # Cache serialization helpers
    def to_json(self) -> str:
        return json.dumps({
            "description": self.description,
            "financials": self.financials,
            "institutional_ownership": self.institutional_ownership,
        })

    @classmethod
    def from_json(cls, s: str) -> StockDescriptiveInfo:
        data = json.loads(s)
        return cls(
            description=data["description"],
            financials=[tuple(pair) for pair in data["financials"]],
            institutional_ownership=[tuple(pair) for pair in data["institutional_ownership"]],
        )
