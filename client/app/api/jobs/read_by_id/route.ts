import { NextRequest, NextResponse } from "next/server";
import { jsonFilePath } from "@/lib/constants";
import { userSchema, UserType } from "@/types/user.types";
import editJsonFile from "edit-json-file";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const id_list: string[] = body.id_list as string[];

    const userDataArray: UserType[] = [];

    const file = editJsonFile(jsonFilePath);

    id_list.forEach((id) => {
      if (file.get(id)) {
        const parsedUserData = userSchema.safeParse(file.get(id));
        if (parsedUserData.success) {
          userDataArray.push(parsedUserData.data);
        }
      }
    });

    return NextResponse.json({ data: userDataArray });
  } catch (err) {
    console.error("Error reading JSON:", err);
    return NextResponse.json({ error: "Failed to read data" }, { status: 500 });
  }
}
