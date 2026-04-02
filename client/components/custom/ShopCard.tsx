"use client";

import { cn } from "@/lib/utils";
import { space_grotesk, jetbrains_mono } from "@/fonts";
import { ShopStatus } from "@/app/api/campus/shops/route";
import {
  ArrowUpRightIcon,
  MapPinIcon,
  StarIcon,
  WifiOffIcon,
} from "lucide-react";
import Link from "next/link";

interface ShopCardProps {
  shop: ShopStatus;
  isBestPick?: boolean;
}

// ── Queue severity colour ──────────────────────────────────────────────────
function queueColor(length: number): string {
  if (length === 0) return "#BEFF72"; // lime  — empty
  if (length <= 3) return "#FFE500"; // yellow — short
  if (length <= 6) return "#FF7A3D"; // orange — medium
  return "#FF5A8A"; // pink   — long
}

// ── Discrete queue-depth indicator (print-ticket aesthetic) ───────────────
function QueueBlocks({ length, color }: { length: number; color: string }) {
  const TOTAL = 10;
  const filled = Math.min(length, TOTAL);
  return (
    <div className="flex items-center gap-[3px]">
      {Array.from({ length: TOTAL }, (_, i) => (
        <div
          key={i}
          className="w-[11px] h-[11px] border-[1.5px] border-foreground shrink-0"
          style={{ background: i < filled ? color : "transparent" }}
        />
      ))}
      {length > TOTAL && (
        <span
          className={cn(
            "text-[10px] font-bold ml-1 leading-none",
            jetbrains_mono.className,
          )}
        >
          +{length - TOTAL}
        </span>
      )}
    </div>
  );
}

// ── Dashed ticket-perforation divider ─────────────────────────────────────
function TicketDivider() {
  return (
    <div className="border-t-2 border-dashed border-foreground/25 -mx-5" />
  );
}

// ── Main component ────────────────────────────────────────────────────────
export default function ShopCard({ shop, isBestPick = false }: ShopCardProps) {
  const uploadUrl = shop.is_self
    ? "/upload"
    : `http://${shop.host}:${shop.port}/upload`;

  const accent = queueColor(shop.queue_length);
  const waitLabel = shop.online
    ? shop.estimated_wait_minutes === 0
      ? "~0 min"
      : `~${shop.estimated_wait_minutes} min`
    : "—";

  // ── Own shop — featured ticket ─────────────────────────────────────────
  if (shop.is_self) {
    return (
      <div
        className="nb-card overflow-hidden flex flex-col"
        style={{ boxShadow: "var(--nb-shadow-lg)" }}
      >
        {/* Yellow identity strip */}
        <div className="bg-primary px-5 py-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <MapPinIcon
              className="h-4 w-4 shrink-0 text-primary-foreground"
              strokeWidth={2.5}
            />
            <span
              className={cn(
                "text-[11px] font-bold tracking-[0.18em] text-primary-foreground",
                jetbrains_mono.className,
              )}
            >
              YOUR LOCATION
            </span>
          </div>
          {isBestPick && (
            <span
              className={cn(
                "flex items-center gap-1 px-2 py-0.5 border-2 border-foreground",
                "text-[10px] font-bold tracking-widest bg-foreground text-background shrink-0",
                jetbrains_mono.className,
              )}
            >
              <StarIcon className="h-2.5 w-2.5" />
              BEST PICK
            </span>
          )}
        </div>

        {/* Shop name */}
        <div className="px-5 pt-4 pb-3">
          <h2
            className={cn(
              "font-black text-2xl leading-tight tracking-tight",
              space_grotesk.className,
            )}
          >
            {shop.shop_name}
          </h2>
          <p
            className={cn(
              "text-[11px] text-muted-foreground mt-0.5",
              jetbrains_mono.className,
            )}
          >
            {shop.host}
          </p>
        </div>

        <TicketDivider />

        {/* Stats */}
        <div className="px-5 py-4 flex flex-col gap-3">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p
                className={cn(
                  "text-[10px] tracking-widest text-muted-foreground mb-1.5",
                  jetbrains_mono.className,
                )}
              >
                QUEUE DEPTH
              </p>
              <QueueBlocks length={shop.queue_length} color={accent} />
            </div>
            <div className="text-right shrink-0">
              <p
                className={cn(
                  "text-[10px] tracking-widest text-muted-foreground mb-0.5",
                  jetbrains_mono.className,
                )}
              >
                WAIT
              </p>
              <p
                className={cn(
                  "font-black text-2xl leading-none tabular-nums",
                  space_grotesk.className,
                )}
              >
                {waitLabel}
              </p>
            </div>
          </div>
        </div>

        <TicketDivider />

        {/* CTA */}
        <div className="px-5 py-4">
          <Link
            href={uploadUrl}
            className={cn(
              "flex items-center justify-center gap-2 w-full",
              "border-2 border-foreground py-3 font-black text-sm tracking-[0.15em]",
              "bg-accent text-accent-foreground transition-all duration-100 nb-press",
              space_grotesk.className,
            )}
            style={{ boxShadow: "var(--nb-shadow-sm)" }}
          >
            UPLOAD HERE
            <ArrowUpRightIcon className="h-4 w-4" strokeWidth={2.5} />
          </Link>
        </div>
      </div>
    );
  }

  // ── Peer shop card ─────────────────────────────────────────────────────
  return (
    <div
      className={cn(
        "nb-card overflow-hidden flex flex-col border-l-[5px]",
        !shop.online && "opacity-55",
      )}
      style={{ borderLeftColor: accent, boxShadow: "var(--nb-shadow)" }}
    >
      {/* Header */}
      <div className="px-5 pt-4 pb-3 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p
            className={cn(
              "text-[10px] tracking-widest text-muted-foreground truncate mb-0.5",
              jetbrains_mono.className,
            )}
          >
            {shop.host}
          </p>
          <h2
            className={cn(
              "font-black text-lg leading-tight tracking-tight",
              space_grotesk.className,
            )}
          >
            {shop.shop_name}
          </h2>
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          {isBestPick && shop.online && (
            <span
              className={cn(
                "flex items-center gap-1 px-2 py-0.5 border-2 border-foreground",
                "text-[10px] font-bold tracking-widest",
                jetbrains_mono.className,
              )}
              style={{ background: "#BEFF72" }}
            >
              <StarIcon className="h-2.5 w-2.5" />
              BEST PICK
            </span>
          )}
          {!shop.online && (
            <span
              className={cn(
                "flex items-center gap-1 px-2 py-0.5 border-2 border-foreground",
                "text-[10px] font-bold tracking-widest text-muted-foreground",
                jetbrains_mono.className,
              )}
            >
              <WifiOffIcon className="h-2.5 w-2.5" />
              OFFLINE
            </span>
          )}
        </div>
      </div>

      <TicketDivider />

      {/* Stats */}
      <div className="px-5 py-4 flex items-center justify-between gap-4">
        <div>
          <p
            className={cn(
              "text-[10px] tracking-widest text-muted-foreground mb-1.5",
              jetbrains_mono.className,
            )}
          >
            QUEUE
          </p>
          {shop.online ? (
            <QueueBlocks length={shop.queue_length} color={accent} />
          ) : (
            <span
              className={cn(
                "text-sm text-muted-foreground",
                jetbrains_mono.className,
              )}
            >
              unavailable
            </span>
          )}
        </div>
        <div className="text-right shrink-0">
          <p
            className={cn(
              "text-[10px] tracking-widest text-muted-foreground mb-0.5",
              jetbrains_mono.className,
            )}
          >
            WAIT
          </p>
          <p
            className={cn(
              "font-black text-xl leading-none tabular-nums",
              space_grotesk.className,
            )}
          >
            {waitLabel}
          </p>
        </div>
      </div>

      <TicketDivider />

      {/* CTA */}
      <div className="px-5 py-4 mt-auto">
        <Link
          href={uploadUrl}
          className={cn(
            "flex items-center justify-center gap-2 w-full",
            "border-2 border-foreground py-2.5 font-black text-sm tracking-[0.15em]",
            "transition-all duration-100",
            shop.online
              ? "bg-primary text-primary-foreground nb-press"
              : "bg-muted text-muted-foreground pointer-events-none",
            space_grotesk.className,
          )}
          style={shop.online ? { boxShadow: "var(--nb-shadow-sm)" } : undefined}
          aria-disabled={!shop.online}
        >
          GO TO SHOP
          <ArrowUpRightIcon className="h-4 w-4" strokeWidth={2.5} />
        </Link>
      </div>
    </div>
  );
}
