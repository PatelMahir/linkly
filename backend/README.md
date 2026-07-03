# Backend — FastAPI service

URL shortener + analytics API. Async end-to-end (FastAPI + SQLAlchemy 2.0 + asyncpg).

## Layered structure

```
app/
├── main.py            # app assembly: middleware + router registration
├── config.py          # typed settings from env (pydantic-settings)
├── database.py        # async engine, session factory, get_db dependency
├── cache.py           # Redis read-through cache for redirects
├── models.py          # ORM tables: Link, ClickEvent  ← the schema
├── schemas.py         # Pydantic request/response contracts
├── routers/           # TRANSPORT: HTTP in/out only, no business logic
│   ├── links.py       #   POST/GET /api/links
│   ├── analytics.py   #   GET /api/analytics/{code}
│   └── redirect.py    #   GET /{code}  (public redirect)
├── services/          # BUSINESS LOGIC: reusable, testable
│   ├── shortener.py   #   create/resolve links, code collisions, caching
│   └── analytics.py   #   record clicks, aggregate stats
└── utils/shortcode.py # secure short-code generation
```

The dependency direction is **routers → services → models/cache**. Routers stay
thin; all logic lives in services so it can be unit-tested without HTTP.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head          # create tables
uvicorn app.main:app --reload
```

Interactive docs: http://localhost:8000/docs

## Key endpoints

| Method | Path                    | Purpose |
|--------|-------------------------|---------|
| POST   | `/api/links`            | Create a short link (optional `custom_code`). |
| GET    | `/api/links`            | List links (newest first). |
| GET    | `/api/analytics/{code}` | Clicks, top referrers, daily timeseries. |
| GET    | `/{code}`               | Redirect + record a click. |
| GET    | `/health`               | Liveness probe. |

## Migrations (Alembic)

```bash
alembic revision --autogenerate -m "add something"   # create a migration
alembic upgrade head                                  # apply
alembic downgrade -1                                  # roll back one
```

## Tests

```bash
pytest -q
```

Tests use an in-memory SQLite DB and a stubbed cache (see `tests/conftest.py`),
so no Postgres/Redis is needed to run them.

## Lint & types

```bash
ruff check . && ruff format .
mypy app
```
