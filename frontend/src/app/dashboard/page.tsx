import LinkTable from "@/components/LinkTable";
import { listLinks, type Link } from "@/lib/api";

// Server Component: fetches on the server at request time. If the API is
// unreachable during a build/preview, we render a friendly empty state.
export default async function DashboardPage() {
  let links: Link[] = [];
  try {
    links = await listLinks();
  } catch {
    links = [];
  }

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-white/60">All your short links and their click counts.</p>
      </div>
      <LinkTable links={links} />
    </section>
  );
}
