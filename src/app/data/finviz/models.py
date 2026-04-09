# Backward-compatibility shim — use domain/models.py instead.
from src.app.domain.models import News, FromRowMixin

__all__ = ["News", "FromRowMixin"]
