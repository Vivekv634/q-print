"use client";
import { space_grotesk, jetbrains_mono } from "@/fonts";
import { cn } from "@/lib/utils";
import { BugIcon, SunMoon } from "lucide-react";
import { Button } from "../ui/button";
import { useTheme } from "next-themes";
import {
  emptyActivityFileStore,
  emptyActivityUserData,
} from "@/db/activity.db";
import { emptyDBUserData, emptyFileSet, emptyFileStore } from "@/db/files.db";

export default function HeadingSection() {
  const { theme, setTheme } = useTheme();

  function clearAll() {
    if (!window.confirm("Clear all local data? This cannot be undone.")) return;
    emptyActivityFileStore();
    emptyActivityUserData();
    emptyDBUserData();
    emptyFileStore();
    emptyFileSet();
  }

  return (
    <section
      className="m-3 nb-card p-5"
    >
      <div className="flex justify-between items-start gap-4">
        <div>
          {/* System label — monospace micro-tag above title */}
          <p className={cn("nb-tag text-muted-foreground mb-2", jetbrains_mono.className)}>
            Campus Print Queue System
          </p>

          {/* Compressed hero title — tight leading like the portfolio */}
          <h1
            className={cn(
              "font-black leading-[0.88] tracking-tight",
              "text-5xl md:text-7xl",
              space_grotesk.className,
            )}
          >
            {/* Acid-yellow slab accent on Q */}
            <span className="bg-primary px-1.5 inline-block">Q</span>
            {"-PRINT"}
          </h1>

          {/* One-line tagline */}
          <p className={cn("mt-3 nb-tag text-muted-foreground", jetbrains_mono.className)}>
            Chaos → Queue → Done
          </p>
        </div>

        {/* Action buttons — shadow-collapse on hover */}
        <div className="flex gap-2 shrink-0 mt-1">
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
            title="Clear all data"
          >
            <BugIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </section>
  );
}
