# Backward-compatibility shim — import from the canonical modules instead.
from src.app.config.settings import Settings, settings
from src.app.config.models import SMART_MODEL, DATA_ANALYSIS_MODEL, MINI_MODEL

__all__ = ["Settings", "settings", "SMART_MODEL", "DATA_ANALYSIS_MODEL", "MINI_MODEL"]
