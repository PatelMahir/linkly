# Frontend — Next.js 15 (App Router)

React 19 + TypeScript + Tailwind CSS v4. Talks to the FastAPI backend over REST.

## Structure

```
src/
├── app/                        # App Router (file-based routing)
│   ├── layout.tsx              # shared shell: nav + <main>
│   ├── page.tsx                # "/"  — shorten form (Server Component)
│   ├── globals.css             # Tailwind import + theme vars
│   └── dashboard/
│       ├── page.tsx            # "/dashboard" — link list (server-fetched)
│       └── [code]/page.tsx     # "/dashboard/:code" — per-link analytics
├── components/
│   ├── ShortenForm.tsx         # "use client" — form state + submit
│   ├── LinkTable.tsx           # presentational table
│   └── AnalyticsChart.tsx      # "use client" — recharts line chart
└── lib/
    └── api.ts                  # typed API client (single source of fetch logic)
```

## Server vs Client Components (the key mental model)

- **Server Components** (default) render on the server. Use them for data fetching
  and static markup — `page.tsx` and `dashboard/page.tsx` fetch directly with `await`.
- **Client Components** (`"use client"`) run in the browser. Use them only when you
  need state, effects, or event handlers — `ShortenForm` and `AnalyticsChart`.

This split keeps JS shipped to the browser small: only interactive bits hydrate.

## Run locally

```bash
npm install
cp .env.example .env.local     # set NEXT_PUBLIC_API_URL
npm run dev                    # http://localhost:3000
```

The backend must be running (see `../backend/README.md`) for data to load.

## Scripts

| Command            | What it does |
|--------------------|--------------|
| `npm run dev`      | Dev server with HMR. |
| `npm run build`    | Production build (standalone output). |
| `npm run lint`     | ESLint (next/core-web-vitals). |
| `npm run typecheck`| `tsc --noEmit`. |
| `npm test`         | Vitest component tests. |

## Notes

- `NEXT_PUBLIC_*` env vars are inlined into the browser bundle — never put secrets there.
- Styling is Tailwind v4, configured via `postcss.config.mjs` (no `tailwind.config.js` needed).
