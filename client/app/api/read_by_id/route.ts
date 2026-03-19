import { NextRequest, NextResponse } from "next/server";
import fs from "fs/promises";
import { jsonFilePath } from "@/lib/constants";
import { UserType } from "@/types/user.types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const id_list: string[] = body.id_list as string[];

    const userDataArray: UserType[] = [];

    const file = await fs.readFile(jsonFilePath, "utf-8");
    const jsonFileData: { [key: string]: UserType } = JSON.parse(file);

    id_list.forEach((id) => {
      userDataArray.push(jsonFileData[id]);
    });

    return NextResponse.json({ data: userDataArray });
  } catch (err) {
    console.error("Error reading JSON:", err);
    return NextResponse.json({ error: "Failed to read data" }, { status: 500 });
  }
}
