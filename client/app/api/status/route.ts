import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { printQueuePath, shopConfigPath } from "@/lib/constants";
import { UserType } from "@/types/user.types";

export async function GET() {
  try {
    const shopConfig = JSON.parse(await readFile(shopConfigPath, "utf-8"));

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
        totalWait === 0 && queueLength > 0
          ? queueLength * 3
          : Math.round(totalWait);
    } catch {
      // queue file missing on first run — queue is empty
    }

    return NextResponse.json({
      shop_name: shopConfig.shop_name as string,
      mdns_hostname: shopConfig.mdns_hostname as string,
      queue_length: queueLength,
      estimated_wait_minutes: estimatedWaitMinutes,
    });
  } catch (error) {
    console.error("Status error:", error);
    return NextResponse.json({ error: "Failed to read status" }, { status: 500 });
  }
}
