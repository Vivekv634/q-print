import { userSchema, UserType } from "@/types/user.types";
import {
  emptyActivityFileStore,
  emptyActivityUserData,
  setActivityUserData,
} from "../activity.db";

export async function fetchFreshData(id_list: string[]): Promise<number> {
  const apiResponse = await fetch("/api/jobs/read_by_id", {
    method: "POST",
    body: JSON.stringify({ id_list }),
  });

  const userDataArray = (await apiResponse.json()).data as UserType[];

  const parsedUserDataArray: UserType[] = [];
  userDataArray.forEach((data) => {
    if (userSchema.safeParse(data).success) {
      parsedUserDataArray.push(data);
    }
  });

  if (parsedUserDataArray.length == 0) {
    emptyActivityFileStore();
    emptyActivityUserData();
  } else {
    Array.from(parsedUserDataArray).forEach((data) => {
      if (data) setActivityUserData(data);
    });
  }
  return parsedUserDataArray.length;
}
