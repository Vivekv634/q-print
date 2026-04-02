import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { mkdir, writeFile } from "fs/promises";
import { userSchema, UserType } from "@/types/user.types";
import { fileStoragePath, jsonFilePath } from "@/lib/constants";
import editJsonFile from "edit-json-file";

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB per file

/*
 1. Retrieve files and userData from formdata; return early if missing.
 2. Parse and validate userData with Zod; return early on failure.
 3. Validate each file: size limit, and _file_id must match a filedataArray entry.
 4. Ensure storage directory exists, write files, then persist userData to JSON.
 5. Return response with userData, message, and file count.
 */

export async function POST(req: NextRequest) {
  try {
    // step 1
    const formData = await req.formData();
    const files = formData.getAll("files") as File[];
    const userdata = formData.get("userData") as unknown;

    if (userdata == null || files.length === 0) {
      return NextResponse.json({ message: "data not found!" }, { status: 404 });
    }

    // step 2
    const userData: UserType = JSON.parse(userdata as string) as UserType;
    const parsedUserData = userSchema.safeParse(userData);

    if (!parsedUserData.success) {
      return NextResponse.json({ message: "can't parse user data" }, { status: 400 });
    }

    // step 3: validate each uploaded file
    const fileIdSet = new Set(parsedUserData.data.filedataArray.map((fd) => fd._file_id));

    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        return NextResponse.json(
          { message: `File "${path.basename(file.name)}" exceeds the 25 MB size limit.` },
          { status: 413 },
        );
      }

      const hasMatchingId = [...fileIdSet].some((id) => file.name.includes(id));
      if (!hasMatchingId) {
        return NextResponse.json(
          { message: "Uploaded file does not match any expected file ID." },
          { status: 400 },
        );
      }
    }

    // step 4: write files first, then persist record (prevents orphaned JSON entries)
    await mkdir(fileStoragePath, { recursive: true });

    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);
      // path.basename strips any directory components — prevents path traversal
      const safeName = path.basename(file.name);
      const file_path = path.join(fileStoragePath, safeName);
      await writeFile(file_path, buffer);
    }

    const jsonFile = editJsonFile(jsonFilePath, { autosave: true });
    jsonFile.set(parsedUserData.data._id, parsedUserData.data);

    // step 5
    return NextResponse.json(
      {
        message: "Upload received",
        fileCount: files.length,
        userData: parsedUserData.data,
      },
      { status: 200 },
    );
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json({ message: "Upload failed" }, { status: 500 });
  }
}
