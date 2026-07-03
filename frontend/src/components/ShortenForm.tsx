"use client";

// Client Component: needs state + event handlers, so it runs in the browser.
import { useState } from "react";
import { createLink, type Link } from "@/lib/api";

export default function ShortenForm() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<Link | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await createLink(url));
      setUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/very/long/url"
          aria-label="Long URL"
          className="flex-1 rounded-lg border border-white/15 bg-white/5 px-4 py-3 outline-none focus:border-indigo-400"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-indigo-500 px-6 py-3 font-medium transition hover:bg-indigo-400 disabled:opacity-50"
        >
          {loading ? "…" : "Shorten"}
        </button>
      </form>

      {error && (
        <p role="alert" className="rounded-lg bg-red-500/15 px-4 py-2 text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-4 py-3">
          <a
            href={result.short_url}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-emerald-300 hover:underline"
          >
            {result.short_url}
          </a>
          <p className="mt-1 truncate text-sm text-white/50">{result.long_url}</p>
        </div>
      )}
    </div>
  );
}
