"use client";

import { space_grotesk, jetbrains_mono } from "@/fonts";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";
import { Toaster } from "sonner";
import { BugIcon, SunMoon, UploadIcon, RefreshCcwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import ShopCard from "@/components/custom/ShopCard";
import { ShopStatus } from "@/app/api/campus/shops/route";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  emptyActivityFileStore,
  emptyActivityUserData,
} from "@/db/activity.db";
import { emptyDBUserData, emptyFileSet, emptyFileStore } from "@/db/files.db";

// ── Loading skeleton — ticket stub shape ───────────────────────────────────
function CardSkeleton({ featured = false }: { featured?: boolean }) {
  return (
    <div
      className={cn(
        "nb-card overflow-hidden animate-pulse",
        featured ? "border-l-0" : "border-l-[5px]",
      )}
      style={{ borderLeftColor: "#EDE8D4" }}
    >
      {featured && <div className="h-12 bg-primary/30" />}
      <div className="px-5 pt-4 pb-3">
        <div className="h-2.5 w-20 bg-muted rounded-none mb-2" />
        <div className="h-6 w-48 bg-muted rounded-none" />
      </div>
      <div className="border-t-2 border-dashed border-foreground/20 -mx-0" />
      <div className="px-5 py-4 flex justify-between">
        <div className="h-3 w-28 bg-muted rounded-none" />
        <div className="h-6 w-16 bg-muted rounded-none" />
      </div>
      <div className="border-t-2 border-dashed border-foreground/20" />
      <div className="px-5 py-4">
        <div className="h-10 w-full bg-muted rounded-none" />
      </div>
    </div>
  );
}

// ── Pulsing live indicator dot ─────────────────────────────────────────────
function LiveDot() {
  return (
    <span className="relative flex h-2 w-2 shrink-0">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75" />
      <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary" />
    </span>
  );
}

// ── Section label divider ──────────────────────────────────────────────────
function SectionLabel({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 my-5">
      <div className="flex-1 h-[2px] bg-foreground/15" />
      <span
        className={cn(
          "text-[10px] font-bold tracking-[0.2em] text-muted-foreground px-1 shrink-0",
          jetbrains_mono.className,
        )}
      >
        {label}
      </span>
      <div className="flex-1 h-[2px] bg-foreground/15" />
    </div>
  );
}

// ── Campus Overview ────────────────────────────────────────────────────────
export default function CampusPage() {
  const { theme, setTheme } = useTheme();
  const [shops, setShops] = useState<ShopStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchShops = useCallback(async () => {
    try {
      const res = await fetch("/api/campus/shops", { cache: "no-store" });
      if (res.ok) {
        const data = (await res.json()) as ShopStatus[];
        setShops(data);
        setLastUpdated(new Date());
      }
    } catch {
      // network error — keep stale data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchShops();
    const interval = setInterval(fetchShops, 15_000);
    return () => clearInterval(interval);
  }, [fetchShops]);

  function clearAll() {
    if (!window.confirm("Clear all local data? This cannot be undone.")) return;
    emptyActivityFileStore();
    emptyActivityUserData();
    emptyDBUserData();
    emptyFileStore();
    emptyFileSet();
  }

  const ownShop = shops.find((s) => s.is_self) ?? null;
  const otherShops = shops
    .filter((s) => !s.is_self)
    .sort((a, b) => {
      // Online shops first, then sort by queue length
      if (a.online !== b.online) return a.online ? -1 : 1;
      return a.queue_length - b.queue_length;
    });

  // Best-pick: among all online shops, lowest queue_length
  const onlineShops = shops.filter((s) => s.online);
  const bestPickHost =
    onlineShops.length > 1
      ? [...onlineShops].sort((a, b) => a.queue_length - b.queue_length)[0].host
      : null;

  return (
    <main className="container mx-auto lg:max-w-1/2 w-full pb-8">
      <Toaster
        position="top-center"
        richColors
        theme={theme === "light" ? "light" : "dark"}
        swipeDirections={["left", "right", "top"]}
      />

      {/* ── Header ──────────────────────────────────────────────────── */}
      <section className="m-3 nb-card p-5">
        <div className="flex justify-between items-start gap-4">
          <div>
            <p className={cn("nb-tag text-muted-foreground mb-2", jetbrains_mono.className)}>
              Campus Print Queue System
            </p>
            <h1
              className={cn(
                "font-black leading-[0.88] tracking-tight text-5xl md:text-7xl",
                space_grotesk.className,
              )}
            >
              <span className="bg-primary px-1.5 inline-block">Q</span>
              {"-PRINT"}
            </h1>
            <p className={cn("mt-3 nb-tag text-muted-foreground", jetbrains_mono.className)}>
              Pick a shop · Upload · Done
            </p>
          </div>

          <div className="flex gap-2 shrink-0 mt-1">
            <Link
              href="/upload"
              className={cn(
                "h-10 px-3 flex items-center gap-1.5 rounded-none border-2 border-foreground",
                "bg-primary text-primary-foreground font-black text-xs tracking-widest nb-press",
                space_grotesk.className,
              )}
              style={{ boxShadow: "var(--nb-shadow-sm)" }}
              title="Upload to this shop"
            >
              <UploadIcon className="h-4 w-4" />
              UPLOAD
            </Link>
            <Button
              className={cn(
                "h-10 w-10 p-0 rounded-none border-2 border-foreground",
                "bg-background text-foreground cursor-pointer nb-press",
                "hover:bg-accent hover:text-accent-foreground",
              )}
              style={{ boxShadow: "var(--nb-shadow-sm)" }}
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              size="icon"
              title="Toggle theme"
            >
              <SunMoon className="h-4 w-4" />
            </Button>
            <Button
              className={cn(
                "h-10 w-10 p-0 rounded-none border-2 border-foreground",
                "bg-background text-foreground cursor-pointer nb-press",
                "hover:bg-destructive hover:text-destructive-foreground",
              )}
              style={{ boxShadow: "var(--nb-shadow-sm)" }}
              onClick={clearAll}
              size="icon"
              title="Clear local data"
            >
              <BugIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* ── Campus board ────────────────────────────────────────────── */}
      <section className="m-3 nb-card p-5">

        {/* Status bar */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <LiveDot />
            <span className={cn("text-[11px] font-bold tracking-[0.15em] text-muted-foreground", jetbrains_mono.className)}>
              LIVE · {loading ? "SCANNING…" : `${shops.length} SHOP${shops.length !== 1 ? "S" : ""} ON CAMPUS`}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {lastUpdated && (
              <span className={cn("text-[10px] text-muted-foreground hidden sm:block", jetbrains_mono.className)}>
                {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <Button
              className={cn(
                "h-7 w-7 p-0 rounded-none border-2 border-foreground",
                "bg-background text-foreground cursor-pointer nb-press",
                "hover:bg-muted",
              )}
              onClick={fetchShops}
              size="icon"
              title="Refresh"
            >
              <RefreshCcwIcon className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* ── This shop (featured, always first) ── */}
        {loading ? (
          <CardSkeleton featured />
        ) : ownShop ? (
          <ShopCard
            shop={ownShop}
            isBestPick={bestPickHost === ownShop.host}
          />
        ) : null}

        {/* ── Other campus shops ── */}
        <SectionLabel
          label={
            loading
              ? "SCANNING CAMPUS NETWORK…"
              : otherShops.length > 0
                ? `${otherShops.length} OTHER SHOP${otherShops.length !== 1 ? "S" : ""} NEARBY`
                : "NO OTHER SHOPS DETECTED"
          }
        />

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : otherShops.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {otherShops.map((shop) => (
              <ShopCard
                key={shop.host}
                shop={shop}
                isBestPick={bestPickHost === shop.host}
              />
            ))}
          </div>
        ) : (
          /* Empty state — scanning animation */
          <div
            className={cn(
              "border-2 border-dashed border-foreground/30 px-6 py-8 text-center",
            )}
          >
            <p className={cn("text-[11px] tracking-[0.2em] text-muted-foreground mb-1", jetbrains_mono.className)}>
              SCANNING NETWORK
            </p>
            <p className={cn("text-sm text-muted-foreground", jetbrains_mono.className)}>
              Other Q-Print shops will appear here automatically when they come online.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
