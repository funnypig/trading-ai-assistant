"""Centralized Langfuse observability setup."""

import asyncio

from langfuse.langchain import CallbackHandler


def get_langfuse_handler() -> CallbackHandler:
    """Create a new per-request Langfuse callback handler."""
    return CallbackHandler()


async def flush_handler(handler: CallbackHandler) -> None:
    """Flush pending trace events without blocking the event loop."""
    await asyncio.get_event_loop().run_in_executor(None, handler.flush)
