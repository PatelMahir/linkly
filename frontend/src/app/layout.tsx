import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Linkly — URL Shortener",
  description: "Shorten URLs and track click analytics.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-white/10">
          <nav className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
            <Link href="/" className="text-lg font-bold tracking-tight">
              🔗 Linkly
            </Link>
            <div className="flex gap-6 text-sm text-white/70">
              <Link href="/" className="hover:text-white">
                Shorten
              </Link>
              <Link href="/dashboard" className="hover:text-white">
                Dashboard
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-4xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
