import type { NextConfig } from "next";
import ipJsonFile from "@/ip.json";

const ip = ipJsonFile.ip_address;

const nextConfig: NextConfig = {
  devIndicators: false,
  allowedDevOrigins: [`${ip}`, `${ip}:3000`],
};

export default nextConfig;
