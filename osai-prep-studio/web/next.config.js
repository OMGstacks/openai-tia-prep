/** @type {import('next').NextConfig} */
// The browser calls the Next app at /api/*, which is proxied server-side to the
// FastAPI grader (osai_spine.api) — no CORS, and the grader URL stays configurable.
const API_URL = process.env.OSAI_API_URL || "http://localhost:8077";

const nextConfig = {
  // Emit a self-contained server bundle for a lean production container image
  // (deploy/Dockerfile.web copies .next/standalone). No-op for `next dev`.
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};

module.exports = nextConfig;
