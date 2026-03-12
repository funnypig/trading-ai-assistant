import logging

import redis

logger = logging.getLogger(__name__)

_pool: redis.ConnectionPool | None = None


def get_redis() -> redis.Redis | None:
    """Return a Redis client from the connection pool, or None if Redis is unavailable."""
    global _pool
    try:
        if _pool is None:
            from src.app.config.config import settings
            _pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
        client = redis.Redis(connection_pool=_pool)
        client.ping()
        return client
    except Exception as exc:
        logger.warning("Redis unavailable: %s — caching disabled", exc)
        return None
