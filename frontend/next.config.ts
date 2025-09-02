import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker runtime image
  output: "standalone",
};

export default nextConfig;
