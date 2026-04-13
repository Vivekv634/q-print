import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  // Allow any *.local origin (mDNS addresses are LAN-only and non-routable).
  // This covers hostname changes made in Settings → Edit Name & Hostname
  // without requiring the dev server to restart.
  allowedDevOrigins: ["*.local"],
};

export default nextConfig;
