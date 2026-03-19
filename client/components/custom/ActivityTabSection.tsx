"use client";

import {
  activityDatabase,
  CustomFileAcitvityObject,
  getAllData,
  UserAcitvityObject,
} from "@/db/activity.db";
import { Activity, useEffect, useState } from "react";
import UserAcitvity from "./UserActivity";
import { Button } from "../ui/button";
import { RefreshCcwIcon } from "lucide-react";
import { fetchFreshData } from "@/db/features/activity.features";

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
  }, []);

  if (!userData) {
    return;
  }

  return (
    <section>
      <section className="flex justify-end mb-4">
        <Button
          variant={"outline"}
          onClick={() => fetchFreshData(Object.keys(userData))}
        >
          Refresh <RefreshCcwIcon />
        </Button>
      </section>
      <section className="flex-col gap-4 flex">
        <Activity mode={userData && files ? "visible" : "hidden"}>
          {Object.values(userData).map((obj, i) => {
            return <UserAcitvity userData={obj} key={i} />;
          })}
        </Activity>
      </section>
    </section>
  );
}
