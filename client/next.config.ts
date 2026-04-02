import type { NextConfig } from "next";
import fs from "fs";
import path from "path";

function getShopHostname(): string {
  try {
    const raw = fs.readFileSync(path.join(__dirname, "shop_config.json"), "utf-8");
    const hostname = (JSON.parse(raw).mdns_hostname as string) ?? "";
    return hostname === "__setup_required__" ? "" : hostname;
  } catch {
    return "";
  }
}

const hostname = getShopHostname();

const nextConfig: NextConfig = {
  devIndicators: false,
  allowedDevOrigins: hostname
    ? [`${hostname}.local`, `${hostname}.local:3000`]
    : [],
};

export default nextConfig;
