import ShortenForm from "@/components/ShortenForm";

// Server Component: static shell. The interactive form is a Client Component.
export default function HomePage() {
  return (
    <section className="space-y-8">
      <div className="space-y-3 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Shorten your links</h1>
        <p className="text-white/60">
          Paste a long URL, get a short one, and track every click.
        </p>
      </div>
      <ShortenForm />
    </section>
  );
}
