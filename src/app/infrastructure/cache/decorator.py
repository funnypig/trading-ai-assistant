import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Set

logger = logging.getLogger(__name__)


def _make_key(func_name: str, args: tuple, kwargs: dict, exclude: Set[str]) -> str:
    safe_kwargs = {k: v for k, v in kwargs.items() if k not in exclude}

    def _default(o):
        if hasattr(o, "name"):  # Enum
            return o.name
        raise TypeError(f"Not JSON-serializable: {type(o)!r}")

    payload = json.dumps(
        {"func": func_name, "args": args, "kwargs": safe_kwargs},
        sort_keys=True,
        default=_default,
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"cache:{func_name}:{digest}"


def redis_cache(
    ttl: int,
    dumps: Callable[[Any], str],
    loads: Callable[[str], Any],
    exclude_kwargs: Set[str] | None = None,
):
    """
    Cache decorator backed by Redis.

    Args:
        ttl: Time-to-live in seconds.
        dumps: Callable that serializes the function return value to a string.
        loads: Callable that deserializes a cached string back to the return type.
        exclude_kwargs: Kwarg names to omit from the cache key (e.g. side-effect
                        params like ``file_path`` that don't affect the data returned).

    Behaviour:
        - If Redis is unavailable the function is called directly (no crash).
        - Redis errors on GET/SET are logged as warnings and never propagate.
    """
    exclude = exclude_kwargs or set()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from src.app.infrastructure.cache.redis_client import get_redis

            client = get_redis()
            if client is None:
                return func(*args, **kwargs)

            key = _make_key(func.__name__, args, kwargs, exclude)

            try:
                cached = client.get(key)
                if cached is not None:
                    logger.debug("Cache HIT  %s", key)
                    return loads(cached)
            except Exception as exc:
                logger.warning("Cache GET failed (%s): %s", key, exc)

            result = func(*args, **kwargs)

            try:
                client.set(key, dumps(result), ex=ttl)
                logger.debug("Cache SET  %s (ttl=%ds)", key, ttl)
            except Exception as exc:
                logger.warning("Cache SET failed (%s): %s", key, exc)

            return result

        return wrapper

    return decorator
