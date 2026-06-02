/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output is only for the Docker image (web/Dockerfile sets
  // DOCKER_BUILD=1). On Netlify/Vercel we use the platform's native build, so
  // we must NOT force standalone there.
  output: process.env.DOCKER_BUILD === "1" ? "standalone" : undefined,
};

export default nextConfig;
