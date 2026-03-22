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
import { RefreshCcwIcon, Space } from "lucide-react";
import { fetchFreshData } from "@/db/features/activity.features";
import { Label } from "../ui/label";
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
    const freshUserDataArrayLength = await fetchFreshData(
      Object.keys(userData),
    );
    console.log(freshUserDataArrayLength);
    if (freshUserDataArrayLength == 0) {
      toast.error("User data not found in the server. Try uploading again!");
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    }
  }

  if (!userData || !files) {
    return;
  }

  return (
    <section>
      <section className="flex justify-end mb-4">
        <Button variant={"outline"} onClick={refreshButtonHandler}>
          Refresh <RefreshCcwIcon />
        </Button>
      </section>
      <section className="flex-col gap-4 flex">
        {userData && files ? (
          <>
            {Object.values(userData).map((obj, i) => {
              return <UserAcitvity userData={obj} key={i} />;
            })}
          </>
        ) : (
          <>
            <Label
              className={cn(
                space_grotesk.className,
                "flex justify-center items-center text-center w-full text-lg font-semibold",
              )}
            >
              No user activity yet.
            </Label>
          </>
        )}
      </section>
    </section>
  );
}
