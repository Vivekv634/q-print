"use client";

import { cn } from "@/lib/utils";
import { space_grotesk, jetbrains_mono, inter } from "@/fonts";
import { BugIcon } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  emptyActivityFileStore,
  emptyActivityUserData,
} from "@/db/activity.db";
import { emptyDBUserData, emptyFileSet, emptyFileStore } from "@/db/files.db";

const ERASED_ITEMS = [
  "On-going print jobs",
  "Already sent print jobs",
  "All uploaded file references",
  "All activity history",
];

interface ClearDataDialogProps {
  trigger: React.ReactNode;
}

export default function ClearDataDialog({ trigger }: ClearDataDialogProps) {
  function clearAll() {
    emptyActivityFileStore();
    emptyActivityUserData();
    emptyDBUserData();
    emptyFileStore();
    emptyFileSet();
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>

      <AlertDialogContent className="rounded-none border-2 border-foreground p-0 overflow-hidden gap-0 max-w-md">

        {/* ── Warning stripe ─────────────────────────────────────────── */}
        <div className="bg-destructive border-b-2 border-foreground px-5 py-3 flex items-center gap-2.5">
          <BugIcon className="h-3.5 w-3.5 shrink-0 text-destructive-foreground" />
          <span
            className={cn(
              "nb-tag tracking-[0.25em] text-destructive-foreground",
              jetbrains_mono.className,
            )}
          >
            Debug · Data Reset
          </span>
        </div>

        {/* ── Body ───────────────────────────────────────────────────── */}
        <div className="px-6 pt-6 pb-5 flex flex-col gap-5">
          <AlertDialogHeader className="gap-1.5 space-y-0 text-left">
            <AlertDialogTitle
              className={cn(
                "text-[1.6rem] font-black leading-[1] tracking-tight",
                space_grotesk.className,
              )}
            >
              Erase all local data?
            </AlertDialogTitle>
            <AlertDialogDescription
              className={cn(
                "text-sm leading-relaxed text-muted-foreground mt-1",
                inter.className,
              )}
            >
              Everything stored in your browser for this shop will be
              permanently wiped.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {/* What gets deleted list */}
          <div className="border-2 border-foreground bg-muted p-4 flex flex-col gap-2.5">
            <p
              className={cn(
                "nb-tag text-muted-foreground mb-0.5",
                jetbrains_mono.className,
              )}
            >
              This includes
            </p>
            {ERASED_ITEMS.map((item) => (
              <div key={item} className="flex items-center gap-2.5">
                <span className="h-1.5 w-1.5 bg-destructive shrink-0" />
                <span className={cn("text-sm font-medium leading-none", inter.className)}>
                  {item}
                </span>
              </div>
            ))}
          </div>

          <p
            className={cn(
              "nb-tag text-muted-foreground",
              jetbrains_mono.className,
            )}
          >
            This action cannot be undone.
          </p>
        </div>

        {/* ── Footer ─────────────────────────────────────────────────── */}
        <AlertDialogFooter className="border-t-2 border-foreground px-6 py-4 bg-muted flex-row gap-3 sm:justify-start">
          <AlertDialogCancel
            className={cn(
              "flex-1 rounded-none border-2 border-foreground bg-background",
              "text-foreground font-black cursor-pointer nb-press m-0",
              space_grotesk.className,
            )}
            style={{ boxShadow: "var(--nb-shadow-sm)" }}
          >
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            className={cn(
              "flex-1 rounded-none border-2 border-foreground",
              "bg-destructive text-destructive-foreground font-black cursor-pointer nb-press",
              "hover:bg-destructive",
              space_grotesk.className,
            )}
            style={{ boxShadow: "var(--nb-shadow-sm)" }}
            onClick={clearAll}
          >
            Yes, erase everything
          </AlertDialogAction>
        </AlertDialogFooter>

      </AlertDialogContent>
    </AlertDialog>
  );
}
