/** @type {import('next').NextConfig} */
const nextConfig = {
  // standalone: bundles only the files needed to run in production.
  // Required for the Docker multi-stage build — generates .next/standalone/
  output: "standalone",

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },
};

module.exports = nextConfig;
