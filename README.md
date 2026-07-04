# Linkly — URL Shortener + Analytics

A production-shaped reference project demonstrating a **modern full-stack architecture**.
Use it as a learning template: every layer (frontend, backend, database, cache, CI/CD, DevOps)
is small enough to read in an afternoon but structured the way a real service would be.

> Domain: shorten long URLs into short codes, redirect visitors, and record click analytics
> (count, referrer, country, timestamp) shown on a dashboard.

---

## Tech stack at a glance

| Layer        | Technology                                   | Why |
|--------------|----------------------------------------------|-----|
| **Frontend** | Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS v4 | SSR/SEO-friendly React with type safety and utility-first styling. |
| **Backend**  | FastAPI · Python 3.12 · Pydantic v2 · SQLAlchemy 2.0 (async) | Fast, typed, auto-documented (OpenAPI) API layer. |
| **Database** | PostgreSQL 16                                | Reliable relational store for links + click events. |
| **Cache**    | Redis 7                                       | Hot redirect lookups and rate limiting. |
| **Messaging**| RabbitMQ 3.13                                 | Async click-analytics ingestion (redirect → queue → worker). |
| **Migrations** | Alembic                                     | Versioned, reversible schema changes. |
| **Tests**    | Pytest (backend) · Vitest (frontend)          | Unit + API tests gated in CI. |
| **CI**       | GitHub Actions                                | Lint → type-check → test → build on every push/PR. |
| **DevOps**   | Docker · Docker Compose                       | One-command local environment; reproducible images. |

---

## Architecture

```
                 ┌────────────────────────┐
   Browser  ───► │  Next.js (frontend)    │  SSR dashboard + shorten form
                 │  localhost:3000        │
                 └───────────┬────────────┘
                             │ REST (JSON) over HTTP
                             ▼
                 ┌────────────────────────┐
                 │  FastAPI (backend)     │  /api/links, /api/analytics, /{code}
                 │  localhost:8000        │
                 └──┬───────┬─────────┬───┘
      reads/writes  │       │ hot     │ publish
                    │       │ lookups │ click
                    ▼       ▼         ▼
          ┌──────────────┐ ┌───────┐ ┌────────────┐
          │ PostgreSQL   │ │ Redis │ │  RabbitMQ  │
          │  links,      │ │ cache │ │  clicks    │
          │  click_events│ └───────┘ └─────┬──────┘
          └──────▲───────┘                 │ consume
                 │      writes click_events │
                 │        ┌─────────────────▼──────┐
                 └────────┤  Worker (app.worker)   │
                          └────────────────────────┘
```

Request flow for a redirect (`GET /{code}`):
1. FastAPI checks **Redis** for `code → {id, url}` (cache hit = no DB touch).
2. On miss, it reads **Postgres** once, then populates Redis with a TTL.
3. It **publishes a click** to **RabbitMQ** and returns a `307` immediately.
4. The **worker** consumes clicks and writes `click_events` to Postgres — so
   redirect latency is decoupled from analytics write throughput.

See [`docs/architecture.md`](docs/architecture.md) for the full write-up and data model.

---

## Repository layout

```
linkly/
├── README.md                 # you are here
├── docker-compose.yml        # postgres + redis + backend + frontend
├── Makefile                  # common dev commands
├── .env.example              # root env for compose
├── .github/workflows/ci.yml  # CI pipeline
├── docs/
│   └── architecture.md       # deep-dive: layers, data model, decisions
├── backend/                  # FastAPI service (see backend/README.md)
│   ├── app/                  #   routers → services → models (layered)
│   ├── migrations/           #   Alembic
│   └── tests/                #   Pytest
└── frontend/                 # Next.js app (see frontend/README.md)
    └── src/app, components, lib
```

---

## Quick start (Docker — recommended)

Prerequisites: Docker Desktop.

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API + Swagger docs: http://localhost:8000/docs
- Postgres: localhost:5432 · Redis: localhost:6379

## Quick start (local, without Docker)

You need Python 3.12, Node 20+, and a running Postgres + Redis.

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## Common commands

```bash
make up          # docker compose up --build
make down        # stop and remove containers
make migrate     # run alembic migrations inside the backend container
make test        # run backend + frontend tests
make lint        # run linters for both apps
```

---

## What to learn from each layer

- **Frontend** — App Router pages, server vs client components, calling an API, and a
  typed API client. Start at [`frontend/src/app/page.tsx`](frontend/src/app/page.tsx).
- **Backend** — layered design (transport → service → data), Pydantic validation, async
  SQLAlchemy, Redis caching. Start at [`backend/app/main.py`](backend/app/main.py).
- **Database** — the schema and indexes in [`backend/app/models.py`](backend/app/models.py)
  and the migration in `backend/migrations/`.
- **CI/CD** — the gates in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- **DevOps** — image builds and service wiring in the `Dockerfile`s and
  [`docker-compose.yml`](docker-compose.yml).

## License

MIT — use it, fork it, learn from it.
