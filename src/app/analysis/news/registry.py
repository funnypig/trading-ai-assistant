"""Run-scoped article registry mapping integer IDs to URLs.

News feed tools register URLs here and expose only the ID to the LLM,
keeping URLs out of the context window.

Uses ContextVar so concurrent agent runs each get an isolated registry
with no cross-contamination. Call init() at the start of each agent run.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class _State:
    registry: dict[int, str] = field(default_factory=dict)  # id → url
    reverse:  dict[str, int] = field(default_factory=dict)  # url → id
    counter:  int = 0


_var: ContextVar[_State] = ContextVar("article_registry")


def _state() -> _State:
    try:
        return _var.get()
    except LookupError:
        s = _State()
        _var.set(s)
        return s


def init() -> None:
    """Initialize a fresh registry for the current context.

    Call once at the start of each agent run to ensure isolation from
    previous runs and from other concurrently running agents.
    """
    _var.set(_State())


def register(url: str) -> int:
    """Store a URL and return its assigned ID.

    Idempotent: the same URL always returns the same ID without incrementing
    the counter, so repeated news feed calls don't bloat the registry.
    """
    s = _state()
    if url in s.reverse:
        return s.reverse[url]
    s.counter += 1
    s.registry[s.counter] = url
    s.reverse[url] = s.counter
    return s.counter


def resolve(article_id: int) -> str | None:
    """Return the URL for a given ID, or None if not registered."""
    return _state().registry.get(article_id)
