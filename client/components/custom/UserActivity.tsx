"use client";
import { UserType } from "@/types/user.types";
import { cn } from "@/lib/utils";
import { space_grotesk, jetbrains_mono } from "@/fonts";
import { Button } from "../ui/button";
import { Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { activityDatabase } from "@/db/activity.db";

/*
 * Print-ticket aesthetic:
 * Left accent bar (6px) encodes queue position via rotating color.
 * No full-card background fill — cleaner, more legible.
 * Shadow-collapse on hover makes the card feel physical.
 */
const TICKET_COLORS = [
  "#FFE500", // yellow   — position 1
  "#BEFF72", // lime     — position 2
  "#00D4E8", // teal     — position 3
  "#FF5A8A", // pink     — position 4
  "#FF7A3D", // orange   — position 5+
];

interface UserAcitvityInterface {
  userData: UserType;
  onDelete: (id: string) => void;
}

export default function UserAcitvity({ userData, onDelete }: UserAcitvityInterface) {
  const [deleting, setDeleting] = useState(false);

  if (!userData) return null;

  const accentColor = TICKET_COLORS[(userData.position - 1) % TICKET_COLORS.length];

  async function handleDelete() {
    setDeleting(true);
    try {
      const res = await fetch("/api/jobs/delete", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: userData._id }),
      });

      if (!res.ok && res.status !== 404) {
        toast.error("Failed to delete job. Try again.");
        return;
      }

      const db = await activityDatabase();
      await db.delete("ACTIVITY USER STORE", userData._id);
      await db.delete("ACTIVITY FILES STORE", userData._id);

      toast.success("Job deleted successfully.");
      onDelete(userData._id);
    } catch {
      toast.error("Error deleting job.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    /*
     * nb-ticket = sharp corners, 6px left border, 5px offset shadow.
     * nb-press = shadow collapses + card translates on hover.
     */
    <div
      id={userData._id}
      className="nb-ticket nb-press"
      style={{ borderLeftColor: accentColor }}
    >
      <div className="p-4">
        {/* Top row: name + position badge + delete */}
        <div className="flex justify-between items-start gap-3">
          <div className="min-w-0">
            <p className={cn("font-black text-lg leading-tight truncate", space_grotesk.className)}>
              {userData.name}
            </p>
            <p className={cn("nb-tag text-muted-foreground mt-1", jetbrains_mono.className)}>
              {new Date(userData.timestamp).toLocaleString("en-IN", { hourCycle: "h12" })}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Ticket number — monospace square badge */}
            <span
              className={cn(
                "font-black text-base w-10 h-10 flex items-center justify-center",
                "border-2 border-foreground",
                jetbrains_mono.className,
              )}
              style={{ background: accentColor }}
            >
              #{userData.position}
            </span>

            {/* Delete — pink, shadow-collapse */}
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "border-2 border-foreground rounded-none bg-destructive text-destructive-foreground",
                "h-10 w-10 nb-press cursor-pointer",
              )}
              style={{ boxShadow: "var(--nb-shadow-xs)" }}
              onClick={handleDelete}
              disabled={deleting}
              title="Delete job"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Separator */}
        <div className="nb-separator my-3" />

        {/* ID footer */}
        <p className={cn("nb-tag text-muted-foreground text-right", jetbrains_mono.className)}>
          ID: {userData._id}
        </p>
      </div>
    </div>
  );
}
