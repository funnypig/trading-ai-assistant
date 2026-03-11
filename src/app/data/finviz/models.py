from dataclasses import dataclass


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
