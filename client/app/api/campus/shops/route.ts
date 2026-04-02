import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { printQueuePath, shopConfigPath, discoveredPeersPath } from "@/lib/constants";
import { UserType } from "@/types/user.types";

interface PeerInfo {
  shop_name: string;
  host: string;
  port: number;
}

export interface ShopStatus {
  shop_name: string;
  host: string;
  port: number;
  queue_length: number;
  estimated_wait_minutes: number;
  is_self: boolean;
  online: boolean;
}

async function getOwnStatus(shopConfig: { shop_name: string; mdns_hostname: string }): Promise<ShopStatus> {
  let queueLength = 0;
  let estimatedWaitMinutes = 0;

  try {
    const queue: UserType[] = JSON.parse(await readFile(printQueuePath, "utf-8"));
    queueLength = queue.length;
    const totalWait = queue.reduce(
      (sum, job) => sum + (job.estimated_time_of_print ?? 0),
      0,
    );
    estimatedWaitMinutes =
      totalWait === 0 && queueLength > 0 ? queueLength * 3 : Math.round(totalWait);
  } catch {
    // queue file missing on first run
  }

  return {
    shop_name: shopConfig.shop_name,
    host: `${shopConfig.mdns_hostname}.local`,
    port: 3000,
    queue_length: queueLength,
    estimated_wait_minutes: estimatedWaitMinutes,
    is_self: true,
    online: true,
  };
}

async function fetchPeerStatus(peer: PeerInfo): Promise<ShopStatus> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(`http://${peer.host}:${peer.port}/api/status`, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);

    if (!res.ok) throw new Error("non-ok response");
    const data = await res.json();

    return {
      shop_name: (data.shop_name as string) ?? peer.shop_name,
      host: peer.host,
      port: peer.port,
      queue_length: (data.queue_length as number) ?? 0,
      estimated_wait_minutes: (data.estimated_wait_minutes as number) ?? 0,
      is_self: false,
      online: true,
    };
  } catch {
    return {
      shop_name: peer.shop_name,
      host: peer.host,
      port: peer.port,
      queue_length: 0,
      estimated_wait_minutes: 0,
      is_self: false,
      online: false,
    };
  }
}

export async function GET() {
  try {
    const shopConfig = JSON.parse(await readFile(shopConfigPath, "utf-8"));
    const ownStatus = await getOwnStatus(shopConfig);

    let peers: PeerInfo[] = [];
    try {
      peers = JSON.parse(await readFile(discoveredPeersPath, "utf-8"));
    } catch {
      // no peers discovered yet
    }

    const peerStatuses = await Promise.all(peers.map(fetchPeerStatus));

    return NextResponse.json([ownStatus, ...peerStatuses]);
  } catch (error) {
    console.error("Campus shops error:", error);
    return NextResponse.json({ error: "Failed to fetch campus data" }, { status: 500 });
  }
}
