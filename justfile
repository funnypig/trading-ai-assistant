up:
    docker network create trading-network || true
    docker compose -f docker-compose.yml up -d
    docker compose -f docker-compose.langfuse.yml up -d

down:
    docker compose -f docker-compose.yml down
    docker compose -f docker-compose.langfuse.yml down

test:
    uv run pytest tests/ -q

query *args:
    PYTHONPATH=. uv run --env-file .env python -m src.app.cli.query {{args}}

run:
    PYTHONPATH=. uv run --env-file .env chainlit run src/app/ui/chainlit_app.py --port 8000

visualize *args:
    OPENAI_API_KEY=dummy PYTHONPATH=. uv run python -m src.app.cli.visualize {{args}}
