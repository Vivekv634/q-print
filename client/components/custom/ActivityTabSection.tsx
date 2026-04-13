"use client";

import {
  activityDatabase,
  CustomFileAcitvityObject,
  getAllData,
  UserAcitvityObject,
} from "@/db/activity.db";
import { useCallback, useEffect, useRef, useState } from "react";
import UserAcitvity from "./UserActivity";
import { Button } from "../ui/button";
import { RefreshCcwIcon } from "lucide-react";
import { fetchFreshData } from "@/db/features/activity.features";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { space_grotesk } from "@/fonts";

async function purgeRejectedFromDB(rejectedIds: string[]): Promise<void> {
  if (rejectedIds.length === 0) return;
  const db = await activityDatabase();
  for (const id of rejectedIds) {
    await db.delete("ACTIVITY USER STORE", id);
    await db.delete("ACTIVITY FILES STORE", id);
  }
}

function showRejectionToasts(rejectedIds: string[]): void {
  rejectedIds.forEach((id) => {
    toast.error("Your print job was rejected by the shop owner.", {
      id: `rejected-${id}`,
      duration: 8000,
      description: `Job ID: ${id}`,
    });
  });
}

const POLL_INTERVAL_MS = 15_000;

export default function ActivityTabSection() {
  const [files, setFiles] = useState<CustomFileAcitvityObject | null>();
  const [userData, setUserData] = useState<UserAcitvityObject | null>();
  const userDataRef = useRef<UserAcitvityObject | null | undefined>(userData);
  userDataRef.current = userData;

  const loadFromDB = useCallback(async () => {
    const res = await getAllData();
    if (res) {
      setFiles(res.fileObject);
      setUserData(res.userObject);
    }
  }, []);

  // Mount: init DB then load once
  useEffect(() => {
    activityDatabase();
    loadFromDB();
  }, [loadFromDB]);

  // Auto-poll: sync with server every 15 s, re-read DB into state after each sync
  useEffect(() => {
    const interval = setInterval(async () => {
      const current = userDataRef.current;
      if (!current) return;
      const ids = Object.keys(current);
      if (ids.length === 0) return;
      const result = await fetchFreshData(ids);
      if (result.rejectedIds.length > 0) {
        showRejectionToasts(result.rejectedIds);
        await purgeRejectedFromDB(result.rejectedIds);
      }
      await loadFromDB();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadFromDB]);

  async function refreshButtonHandler() {
    if (!userData) return;
    const result = await fetchFreshData(Object.keys(userData));
    if (result.rejectedIds.length > 0) {
      showRejectionToasts(result.rejectedIds);
      await purgeRejectedFromDB(result.rejectedIds);
    }
    if (result.count === 0 && result.rejectedIds.length === 0) {
      toast.error("User data not found in the server. Try uploading again!");
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    }
    await loadFromDB();
  }

  if (!userData || !files) {
    return null;
  }

  const jobCount = Object.keys(userData).length;

  return (
    <section>
      {/* Header row */}
      <div className="flex justify-between items-center mb-4">
        {/* Job count badge */}
        <span
          className="nb-tag px-2 py-1 border-2 border-foreground bg-accent text-accent-foreground"
        >
          {jobCount} job{jobCount !== 1 ? "s" : ""} tracked
        </span>

        {/* Refresh — shadow-collapse */}
        <Button
          onClick={refreshButtonHandler}
          className={cn(
            "border-2 border-foreground rounded-none bg-background text-foreground",
            "font-bold cursor-pointer nb-press gap-2",
            space_grotesk.className,
          )}
          style={{ boxShadow: "var(--nb-shadow-sm)" }}
        >
          <RefreshCcwIcon className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Activity ticket list */}
      <section className="flex flex-col gap-3">
        {jobCount > 0 ? (
          Object.values(userData).map((obj, i) => (
            <UserAcitvity
              userData={obj}
              key={i}
              onDelete={(id) =>
                setUserData((prev) => {
                  if (!prev) return prev;
                  const updated = { ...prev };
                  delete updated[id];
                  return updated;
                })
              }
            />
          ))
        ) : (
          <p className="text-center nb-tag py-8 text-muted-foreground">
            No jobs tracked yet. Upload a file to start.
          </p>
        )}
      </section>
    </section>
  );
}
