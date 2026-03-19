import { UserType } from "@/types/user.types";
import { setActivityUserData } from "../activity.db";

export async function fetchFreshData(id_list: string[]) {
  const apiResponse = await fetch("/api/read_by_id", {
    method: "POST",
    body: JSON.stringify({ id_list }),
  });

  const userDataArray = (await apiResponse.json()).data as UserType[];

  Array.from(userDataArray).forEach((data) => {
    setActivityUserData(data);
  });
}
