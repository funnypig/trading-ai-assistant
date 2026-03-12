test:
    uv run pytest tests/ -q

query *args:
    PYTHONPATH=. uv run --env-file .env python -m src.app.cli.query {{args}}

run:
    PYTHONPATH=. uv run --env-file .env chainlit run src/app/ui/chainlit_app.py --port 8000
