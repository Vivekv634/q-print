"use client";

import {
  activityDatabase,
  CustomFileAcitvityObject,
  getAllActivityUserData,
  getAllData,
  UserAcitvityObject,
} from "@/db/activity.db";
import { useEffect, useState } from "react";
import UserAcitvity from "./UserActivity";
import { Button } from "../ui/button";
import { RefreshCcwIcon } from "lucide-react";
import { fetchFreshData } from "@/db/features/activity.features";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { space_grotesk } from "@/fonts";

export default function ActivityTabSection() {
  const [files, setFiles] = useState<CustomFileAcitvityObject | null>();
  const [userData, setUserData] = useState<UserAcitvityObject | null>();

  useEffect(() => {
    activityDatabase();
    getAllData().then((res) => {
      if (res) {
        setFiles(res.fileObject);
        setUserData(res.userObject);
      }
    });
    if (userData) {
      fetchFreshData(Object.keys(userData));
      getAllActivityUserData();
    }
  }, []);

  async function refreshButtonHandler() {
    if (!userData) return;
    const freshUserDataArrayLength = await fetchFreshData(Object.keys(userData));
    if (freshUserDataArrayLength == 0) {
      toast.error("User data not found in the server. Try uploading again!");
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    }
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
