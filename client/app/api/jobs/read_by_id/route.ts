import { NextRequest, NextResponse } from "next/server";
import { userSchema, UserType } from "@/types/user.types";
import { USER_ID_LENGTH, PYTHON_API_URL } from "@/lib/constants";
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

    const res = await fetch(`${PYTHON_API_URL}/jobs/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_list: parsed.data.id_list }),
    });

    if (!res.ok) {
      throw new Error(`Python API returned ${res.status}`);
    }

    const raw: unknown[] = await res.json();
    const userDataArray: UserType[] = raw
      .map((item) => userSchema.safeParse(item))
      .filter((r) => r.success)
      .map((r) => (r as { success: true; data: UserType }).data);

    return NextResponse.json({ data: userDataArray });
  } catch (err) {
    console.error("Error reading jobs:", err);
    return NextResponse.json({ error: "Failed to read data" }, { status: 500 });
  }
}
