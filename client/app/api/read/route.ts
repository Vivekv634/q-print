import { NextRequest, NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

export async function GET(request: NextRequest) {
  try {
    const name_paramter = request.nextUrl.searchParams.get("name");
    if (!name_paramter)
      return NextResponse.json({ error: "name not found" }, { status: 300 });

    const filePath = path.join(process.cwd(), "user_records.json");

    const file = await fs.readFile(filePath, "utf-8");
    const data: { [key: string]: string } = JSON.parse(file);

    return NextResponse.json(data[name_paramter]);
  } catch (err) {
    console.error("Error reading JSON:", err);
    return NextResponse.json({ error: "Failed to read data" }, { status: 500 });
  }
}
