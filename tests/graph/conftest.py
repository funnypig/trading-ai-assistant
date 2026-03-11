import os

# Set dummy credentials before any agent/config modules are imported.
# Actual API calls are never made in graph tests — all nodes are mocked.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("FINVIZ_API_KEY", "test-key")
os.environ.setdefault("FINVIZ_EMAIL", "test@test.com")
os.environ.setdefault("FINVIZ_PASSWORD", "test-password")
os.environ.setdefault("PLAYWRIGHT_USER_DATA_DIR", "/tmp")
