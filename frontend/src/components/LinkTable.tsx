import NextLink from "next/link";
import type { Link } from "@/lib/api";

export default function LinkTable({ links }: { links: Link[] }) {
  if (links.length === 0) {
    return (
      <p className="rounded-lg border border-white/10 bg-white/5 px-4 py-8 text-center text-white/50">
        No links yet. Create one from the{" "}
        <NextLink href="/" className="text-indigo-300 hover:underline">
          home page
        </NextLink>
        .
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-white/10">
      <table className="w-full text-left text-sm">
        <thead className="bg-white/5 text-white/60">
          <tr>
            <th className="px-4 py-3 font-medium">Short</th>
            <th className="px-4 py-3 font-medium">Destination</th>
            <th className="px-4 py-3 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          {links.map((link) => (
            <tr key={link.id} className="border-t border-white/10">
              <td className="px-4 py-3">
                <NextLink
                  href={`/dashboard/${link.code}`}
                  className="font-mono text-indigo-300 hover:underline"
                >
                  /{link.code}
                </NextLink>
              </td>
              <td className="max-w-xs truncate px-4 py-3 text-white/70">{link.long_url}</td>
              <td className="px-4 py-3 text-white/50">
                {new Date(link.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
