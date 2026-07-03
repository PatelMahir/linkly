import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Produces a minimal standalone server bundle for smaller Docker images.
  output: "standalone",
};

export default nextConfig;
