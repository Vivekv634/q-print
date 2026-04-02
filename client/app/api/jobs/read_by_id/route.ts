import { NextRequest, NextResponse } from "next/server";
import { jsonFilePath } from "@/lib/constants";
import { userSchema, UserType } from "@/types/user.types";
import { USER_ID_LENGTH } from "@/lib/constants";
import editJsonFile from "edit-json-file";
import z from "zod";

const requestSchema = z.object({
  id_list: z.array(z.string().length(USER_ID_LENGTH)).max(100),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = requestSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
    }

    const { id_list } = parsed.data;
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
