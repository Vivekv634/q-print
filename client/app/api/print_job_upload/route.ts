import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { writeFile } from "fs/promises";
import { userSchema, UserType } from "@/types/user.types";
import { appendToJSON, fileStoragePath } from "@/lib/constants";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    const files = formData.getAll("files") as File[];
    const userdata = formData.get("userData") as unknown;

    if (userdata == null) {
      return NextResponse.json(
        { message: "userdata not found!" },
        { status: 404 },
      );
    }

    const userData: UserType = JSON.parse(userdata as string) as UserType;
    const parsedUserData = userSchema.safeParse(userData);

    if (!parsedUserData.success) {
      return NextResponse.json(
        {
          message: "can't parse user data",
        },
        { status: 500 },
      );
    }

    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);

      const file_path = path.join(fileStoragePath, file.name);

      await writeFile(file_path, buffer);
    }

    appendToJSON(userData);

    return NextResponse.json(
      {
        message: "Upload received",
        fileCount: files.length,
        userData,
      },
      { status: 200 },
    );
  } catch (error) {
    console.error(error);
    return NextResponse.json({ message: "Upload failed" }, { status: 500 });
  }
}
