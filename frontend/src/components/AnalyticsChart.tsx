"use client";

// Recharts renders on the client, so this is a Client Component.
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ClickPoint } from "@/lib/api";

export default function AnalyticsChart({ data }: { data: ClickPoint[] }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-white/40">No clicks recorded yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
        <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" fontSize={12} />
        <YAxis allowDecimals={false} stroke="rgba(255,255,255,0.4)" fontSize={12} />
        <Tooltip
          contentStyle={{
            background: "#0b1020",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: 8,
          }}
        />
        <Line type="monotone" dataKey="clicks" stroke="#818cf8" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
