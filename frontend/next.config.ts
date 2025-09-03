import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker runtime image
  output: "standalone",
  // Ensure ESM packages in node_modules are transpiled for Next/Turbopack
  transpilePackages: ["audiomotion-analyzer"],
  // Avoid failing builds due to ESLint issues elsewhere in the repo
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
