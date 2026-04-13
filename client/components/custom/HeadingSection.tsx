"use client";
import { space_grotesk, jetbrains_mono } from "@/fonts";
import { cn } from "@/lib/utils";
import { BugIcon, SunMoon } from "lucide-react";
import { Button } from "../ui/button";
import { useTheme } from "next-themes";
import ClearDataDialog from "./ClearDataDialog";

export default function HeadingSection() {
  const { theme, setTheme } = useTheme();

  return (
    <section className="m-3 nb-card p-5">
      <div className="flex justify-between items-start gap-4">
        <div>
          <p className={cn("nb-tag text-muted-foreground mb-2", jetbrains_mono.className)}>
            Campus Print Queue System
          </p>
          <h1
            className={cn(
              "font-black leading-[0.88] tracking-tight",
              "text-5xl md:text-7xl",
              space_grotesk.className,
            )}
          >
            <span className="bg-primary px-1.5 inline-block">Q</span>
            {"-PRINT"}
          </h1>
          <p className={cn("mt-3 nb-tag text-muted-foreground", jetbrains_mono.className)}>
            Chaos → Queue → Done
          </p>
        </div>

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

          <ClearDataDialog
            trigger={
              <Button
                className={cn(
                  "h-10 w-10 p-0 rounded-none border-2 border-foreground",
                  "bg-background text-foreground cursor-pointer nb-press",
                  "hover:bg-destructive hover:text-destructive-foreground",
                )}
                style={{ boxShadow: "var(--nb-shadow-sm)" }}
                size="icon"
                title="Clear all data"
              >
                <BugIcon className="h-4 w-4" />
              </Button>
            }
          />
        </div>
      </div>
    </section>
  );
}
