import { NextRequest, NextResponse } from "next/server";
import { jsonFilePath, USER_ID_LENGTH } from "@/lib/constants";
import editJsonFile from "edit-json-file";
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

    const { id } = parsed.data;
    const file = editJsonFile(jsonFilePath, { autosave: true });

    if (!file.get(id)) {
      return NextResponse.json({ message: "record not found" }, { status: 404 });
    }

    file.unset(id);
    return NextResponse.json({ message: "deleted" }, { status: 200 });
  } catch (err) {
    console.error("Delete error:", err);
    return NextResponse.json({ message: "Failed to delete record" }, { status: 500 });
  }
}
