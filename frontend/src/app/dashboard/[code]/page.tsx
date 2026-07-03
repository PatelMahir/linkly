import AnalyticsChart from "@/components/AnalyticsChart";
import { getAnalytics } from "@/lib/api";

// Per-link analytics detail. `code` comes from the dynamic route segment.
export default async function LinkAnalyticsPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  const stats = await getAnalytics(code);

  return (
    <section className="space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold">/{stats.code}</h1>
        <p className="text-white/60">{stats.total_clicks} total clicks</p>
      </div>

      <div className="rounded-lg border border-white/10 bg-white/5 p-4">
        <h2 className="mb-4 text-sm font-medium text-white/60">Clicks over time</h2>
        <AnalyticsChart data={stats.timeseries} />
      </div>

      <div className="rounded-lg border border-white/10 bg-white/5 p-4">
        <h2 className="mb-3 text-sm font-medium text-white/60">Top referrers</h2>
        <ul className="space-y-1 text-sm">
          {stats.top_referrers.map(([ref, count]) => (
            <li key={ref} className="flex justify-between">
              <span className="text-white/70">{ref}</span>
              <span className="font-mono text-white/50">{count}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
