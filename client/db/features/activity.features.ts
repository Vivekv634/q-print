import { userSchema, UserType } from "@/types/user.types";
import {
  emptyActivityFileStore,
  emptyActivityUserData,
  setActivityUserData,
} from "../activity.db";

export interface FetchFreshDataResult {
  count: number;
  rejectedIds: string[];
}

export async function fetchFreshData(id_list: string[]): Promise<FetchFreshDataResult> {
  const apiResponse = await fetch("/api/jobs/read_by_id", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_list }),
  });

  if (!apiResponse.ok) {
    return { count: 0, rejectedIds: [] };
  }

  const responseData = await apiResponse.json();
  const userDataArray = (responseData.data ?? []) as UserType[];
  const rejectedIds = (responseData.rejected_ids ?? []) as string[];

  const parsedUserDataArray: UserType[] = [];
  userDataArray.forEach((data) => {
    if (userSchema.safeParse(data).success) {
      parsedUserDataArray.push(data);
    }
  });

  if (parsedUserDataArray.length === 0) {
    await emptyActivityFileStore();
    await emptyActivityUserData();
  } else {
    for (const data of parsedUserDataArray) {
      await setActivityUserData(data);
    }
  }

  return { count: parsedUserDataArray.length, rejectedIds };
}
