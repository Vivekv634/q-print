import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { writeFile } from "fs/promises";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    const files = formData.getAll("files") as File[];
    const userdata = formData.get("userData");

    const file_storage_folder_path = path.join(
      process.cwd(),
      "print_job_file_storage",
    );

    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);

      const file_path = path.join(file_storage_folder_path, file.name);

      await writeFile(file_path, buffer);
    }
    return NextResponse.json(
      {
        message: "Upload received",
        fileCount: files.length,
        userdata,
      },
      { status: 200 },
    );
  } catch (error) {
    console.error(error);
    return NextResponse.json({ message: "Upload failed" }, { status: 500 });
  }
}
