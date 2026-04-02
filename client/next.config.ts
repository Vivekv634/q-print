import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  allowedDevOrigins: ["qprint.local", "qprint.local:3000"],
};

export default nextConfig;
