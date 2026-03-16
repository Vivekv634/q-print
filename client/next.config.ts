import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  devIndicators: false,
  allowedDevOrigins: ["192.168.29.23", "http://192.168.29.23:*"],
};

export default nextConfig;
