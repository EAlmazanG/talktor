/**
 * Next.js configuration for Talktor
 * - Set output to standalone so the production Dockerfile can run `node server.js`
 * - Keep settings minimal and compatible with Next 15
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // During CI/containers we prefer not to fail builds on lint
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
