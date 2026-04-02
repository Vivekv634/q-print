/**
 * Detects the machine's local network IP and writes it to ip.json.
 * Runs automatically as a `predev` npm hook before `next dev` starts.
 * Uses only Node.js built-ins — no extra dependencies.
 */

import { networkInterfaces } from "os";
import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function getLocalIp() {
  const nets = networkInterfaces();
  for (const name of Object.keys(nets)) {
    if (name === "lo" || name === "lo0") continue; // skip loopback
    for (const net of nets[name]) {
      if (net.family === "IPv4" && !net.internal) {
        return net.address;
      }
    }
  }
  return "127.0.0.1"; // fallback
}

const ip = getLocalIp();
const outputPath = join(__dirname, "..", "ip.json");
writeFileSync(outputPath, JSON.stringify({ ip_address: ip }, null, 2));
console.log(`[q-print] Local IP detected: ${ip}`);
