import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { mkdir, writeFile } from "fs/promises";
import { userSchema, UserType } from "@/types/user.types";
import { fileStoragePath, PYTHON_API_URL } from "@/lib/constants";

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB per file

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const files = formData.getAll("files") as File[];
    const userdata = formData.get("userData") as unknown;

    if (userdata == null || files.length === 0) {
      return NextResponse.json({ message: "data not found!" }, { status: 404 });
    }

    const userData: UserType = JSON.parse(userdata as string) as UserType;
    const parsedUserData = userSchema.safeParse(userData);

    if (!parsedUserData.success) {
      return NextResponse.json({ message: "can't parse user data" }, { status: 400 });
    }

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

    // Write files to disk first — prevents orphaned queue entries if upload fails
    await mkdir(fileStoragePath, { recursive: true });
    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const safeName = path.basename(file.name);
      await writeFile(path.join(fileStoragePath, safeName), Buffer.from(bytes));
    }

    // Register job in Python queue — serialized through write queue
    const res = await fetch(`${PYTHON_API_URL}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsedUserData.data),
    });

    if (!res.ok) {
      throw new Error(`Python API returned ${res.status}`);
    }

    return NextResponse.json(
      { message: "Upload received", fileCount: files.length, userData: parsedUserData.data },
      { status: 200 },
    );
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json({ message: "Upload failed" }, { status: 500 });
  }
}
