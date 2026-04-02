import { userSchema, UserType } from "@/types/user.types";
import {
  emptyActivityFileStore,
  emptyActivityUserData,
  setActivityUserData,
} from "../activity.db";

export async function fetchFreshData(id_list: string[]): Promise<number> {
  const apiResponse = await fetch("/api/jobs/read_by_id", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_list }),
  });

  if (!apiResponse.ok) {
    return 0;
  }

  const userDataArray = (await apiResponse.json()).data as UserType[];

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

  return parsedUserDataArray.length;
}
