# Legal OS - Foundation Layer

Minimal scaffold for the Legal Document Processing Pipeline API.

## Quick start

1) Install Poetry (if you don't have it): https://python-poetry.org/

2) Install dependencies:

```bash
poetry install
```

3) Run tests:

```bash
poetry run pytest
```

4) Launch the API locally:

```bash
poetry run uvicorn legal_os.main:app --reload
```

Health check at `http://127.0.0.1:8000/health`.

## Postgres with Docker Compose (optional)

Run a local Postgres 16 via Docker Compose:

```bash
docker compose --env-file .env.compose up -d postgres
```

Set your `.env` to point to Postgres (or copy from `.env.compose`):

```bash
cp .env.compose .env
```

Apply database migrations:

```bash
source .venv/bin/activate
alembic upgrade head
```

To generate new migrations after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Dev tools
- Black, isort, flake8, mypy
- pytest with httpx TestClient
- pre-commit hooks: `poetry run pre-commit install`

## Notes
This is Phase 0.1.x scaffolding. DB foundation (SQLAlchemy + Alembic) is included; optional Postgres via Compose.
