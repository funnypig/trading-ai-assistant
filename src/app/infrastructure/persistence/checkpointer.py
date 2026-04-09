"""PostgreSQL checkpointer factory for LangGraph conversation persistence."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection

from src.app.config.settings import settings


async def create_postgres_checkpointer() -> AsyncPostgresSaver:
    """Create and set up an AsyncPostgresSaver backed by Supabase."""
    conn = await AsyncConnection.connect(settings.supabase_db_url, autocommit=True)
    checkpointer = AsyncPostgresSaver(conn)
    await checkpointer.setup()
    return checkpointer
