# Architecture & Design Notes

A deeper look at how Linkly is put together and *why*, so you can reason about
each layer and adapt the patterns to your own projects.

## 1. System overview

Linkly is a two-service app plus two stateful backing services:

| Component | Runtime | Responsibility |
|-----------|---------|----------------|
| Frontend  | Next.js (Node) | UI, SSR, calls the API. |
| Backend   | FastAPI (Python) | REST API, redirects, business logic. |
| Postgres  | —       | Source of truth: links + click events. |
| Redis     | —       | Cache for hot redirect lookups; rate-limit primitive. |

They run as four containers via `docker-compose.yml`. In production you'd deploy
frontend and backend independently (e.g. Vercel + a container platform) and use
managed Postgres/Redis.

## 2. Data model

```
links                              click_events
─────                              ────────────
id           PK                    id            PK
code         UNIQUE, INDEX  ◄──────link_id       FK → links.id, INDEX
long_url                           referrer      NULL
created_at   INDEX                 country       NULL (ISO-2)
                                   user_agent    NULL
                                   created_at    INDEX
```

Design choices:
- **`click_events` is append-only.** We never update a click; we insert one per
  redirect. Aggregations (totals, timeseries) are computed at read time with
  `GROUP BY`. For high volume you'd later add a rollup table or a warehouse.
- **Indexes match read patterns.** `links.code` (redirect lookup), `click_events.link_id`
  (per-link analytics), `click_events.created_at` (time-range queries).
- **`ON DELETE CASCADE`** keeps analytics consistent when a link is removed.

## 3. Backend layering

```
HTTP  →  routers/   (transport: parse, validate, shape responses)
         services/  (business logic: reusable, unit-testable)
         models/    (ORM) + cache/ (Redis)  →  Postgres / Redis
```

Rationale: routers stay thin so logic isn't tied to HTTP and can be tested
directly. Services own transactions and the DB/cache. This is the standard
transport → service → data-access split from the coding standards.

### Redirect hot path
1. `resolve_code` checks Redis for `code → long_url`.
2. On miss, read Postgres and populate Redis with a TTL (`cache_ttl_seconds`).
3. Record a click event, then return `307`.

Caching matters because redirects are the dominant traffic and are read-heavy
with rarely-changing data — an ideal cache candidate.

## 4. Frontend rendering strategy

- **Server Components by default** for data fetching (`dashboard/page.tsx` awaits
  the API on the server). Smaller JS bundles, better SEO, no client fetch waterfalls.
- **Client Components only where interactivity is required** (`ShortenForm`,
  `AnalyticsChart`). Marked with `"use client"`.
- **One typed API client** (`lib/api.ts`) is the only place that knows URLs and
  response shapes, so types propagate to every component.

## 5. Trade-offs & what you'd add for production

| Area | Current (reference) | Production next step |
|------|---------------------|----------------------|
| Auth | none | Sessions/JWT + per-user link ownership (authz on every path). |
| Analytics | background ingestion + live `GROUP BY` | Queue (RabbitMQ/BullMQ) + rollup tables for high volume. |
| Rate limiting | ✅ Redis fixed-window per IP on create + redirect | Sliding-window / token-bucket; per-API-key quotas. |
| Redirect path | ✅ Redis read-through cache; non-blocking click writes | Edge cache / CDN in front for global latency. |
| Health | ✅ `/health` liveness + `/ready` (DB + Redis) | Add dependency-level SLOs and alerting. |
| Observability | ✅ request-id + latency headers | Structured logs, metrics export (Prometheus), tracing. |
| Secrets | `.env` files | Secret manager (AWS/Azure), never in the image. |
| Deploys | Docker images | Blue/green or canary (see team runbooks). |

### How this branch scales the service

1. **Redirects are the hottest path**, so we (a) serve them from a Redis
   read-through cache — a cache hit never touches Postgres — and (b) move the
   click write into a `BackgroundTask` so the redirect response isn't blocked by
   an `INSERT`. Under load these two changes cut both DB reads and p99 latency.
2. **Rate limiting** (Redis `INCR` + `EXPIRE`, O(1) per request) caps abuse and
   protects the DB from stampedes — applied to link creation and redirects.
3. **`/ready`** lets an orchestrator drain and shift traffic safely during
   rolling / blue-green / canary rollouts (a pod can be *up* but not *ready*).
4. **Pagination** keeps the list endpoint bounded as link counts grow.
5. **Request-id + timing headers** make requests traceable across services.

## 6. Security notes

- Input validated at the boundary with Pydantic (`HttpUrl`, code pattern).
- Parameterized queries via SQLAlchemy (no string-built SQL → no injection).
- Containers run as a **non-root** user.
- No secrets in code, logs, or `NEXT_PUBLIC_*` vars.
- CORS restricted to configured origins.

These map to the PCI-DSS / SOC 2 gates: validate input, least privilege,
parameterized queries, no secrets in code, authz on protected paths (to add
with auth).
