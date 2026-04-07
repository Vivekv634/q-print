import { NextRequest, NextResponse } from "next/server";
import { USER_ID_LENGTH, PYTHON_API_URL } from "@/lib/constants";
import z from "zod";

const deleteSchema = z.object({
  id: z.string().length(USER_ID_LENGTH),
});

export async function DELETE(request: NextRequest) {
  try {
    const body: unknown = await request.json();
    const parsed = deleteSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ message: "Invalid request body" }, { status: 400 });
    }

    const res = await fetch(`${PYTHON_API_URL}/jobs/${parsed.data.id}`, {
      method: "DELETE",
    });

    if (res.status === 404) {
      return NextResponse.json({ message: "record not found" }, { status: 404 });
    }
    if (!res.ok) {
      throw new Error(`Python API returned ${res.status}`);
    }

    return NextResponse.json({ message: "deleted" }, { status: 200 });
  } catch (err) {
    console.error("Delete error:", err);
    return NextResponse.json({ message: "Failed to delete record" }, { status: 500 });
  }
}
