// Typed API client. One place that knows how to talk to the backend, so
// components stay dumb and types flow from here.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Link {
  id: number;
  code: string;
  long_url: string;
  short_url: string;
  created_at: string;
}

export interface ClickPoint {
  date: string;
  clicks: number;
}

export interface LinkAnalytics {
  code: string;
  total_clicks: number;
  top_referrers: [string, number][];
  timeseries: ClickPoint[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function createLink(longUrl: string, customCode?: string): Promise<Link> {
  return request<Link>("/api/links", {
    method: "POST",
    body: JSON.stringify({ long_url: longUrl, custom_code: customCode || null }),
  });
}

export function listLinks(limit = 20, offset = 0): Promise<Link[]> {
  // Paginated so the dashboard stays fast as the number of links grows.
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return request<Link[]>(`/api/links?${query}`, { cache: "no-store" });
}

export function getAnalytics(code: string): Promise<LinkAnalytics> {
  return request<LinkAnalytics>(`/api/analytics/${code}`, { cache: "no-store" });
}
