/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Minimal standalone server bundle for Docker-based hosts (Fly/Render).
  // Vercel ignores this and builds natively.
  output: "standalone",
};

export default nextConfig;
