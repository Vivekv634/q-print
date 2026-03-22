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
    emptyActivityFileStore();
    emptyActivityUserData();
    emptyDBUserData();
    emptyFileStore();
    emptyFileSet();
  }

  return (
    <section className="m-3 border-inherit border-2 p-5 rounded-2xl bg-background text-foreground border-b-[5px] border-r-[5px]">
      {/* heading section */}
      <section>
        <div className="flex justify-between">
          <h1
            className={cn(
              "font-extrabold text-3xl md:text-5xl",
              space_grotesk.className,
            )}
          >
            Q-PRINT
          </h1>
          <div>
            <Button
              className="rounded-full border-2 border-b-4 border-r-4 bg-background cursor-pointer text-foreground border-foreground p-3 h-10 w-10"
              onClick={() => setTheme(theme == "light" ? "dark" : "light")}
              size={"icon"}
            >
              <SunMoon className="h-5 w-5" />
            </Button>
            <Button
              className="rounded-full border-2 border-b-4 border-r-4 bg-background cursor-pointer text-foreground border-foreground p-3 h-10 w-10"
              onClick={clearAll}
              size={"icon"}
            >
              <BugIcon className="h-5 w-5" />
            </Button>
          </div>
        </div>
        <h3 className={cn("font-medium", jetbrains_mono.className)}>
          Simplifying print chaos into manageable queues.
        </h3>
      </section>
    </section>
  );
}
