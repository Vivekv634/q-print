import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { writeFile } from "fs/promises";
import { userSchema, UserType } from "@/types/user.types";
import { fileStoragePath, jsonFilePath } from "@/lib/constants";
import editJsonFile from "edit-json-file";

/*
 1. retrive the data like the files and the userdata from the formdata and return early if data not found.
 2. parse the userdata before append to the json file and if error occurs then return early with the proper status code.
 3. parse and match the file's id with the userdata's filedataArray and if not matched then return early with the status code.
 4. after doing checks, save the userdata and files at their pre-defined file and folder respectively.
 5. return the response including the userdata, message, file count & status code.
 */

export async function POST(req: NextRequest) {
  try {
    // step 1 starts
    const formData = await req.formData();

    const files = formData.getAll("files") as File[];
    const userdata = formData.get("userData") as unknown;

    if (userdata == null || files.length == 0) {
      return NextResponse.json({ message: "data not found!" }, { status: 404 });
    }
    // step 1 ends

    // step 2 starts
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

    // step 2 ends

    // step 3 starts
    const filename_set: Set<string> = new Set<string>();
    userData.filedataArray.forEach((FD) => filename_set.add(FD.file_name));

    files.forEach((F) => {
      console.log(F.name.split("_")[1], filename_set.has(F.name.split("_")[1]));
      if (!filename_set.has(F.name.split("_")[1])) {
        return NextResponse.json(
          {
            message: "file name didn't match.",
          },
          { status: 500 },
        );
      }
    });
    // step 3 ends

    // step 4 starts
    const jsonFile = editJsonFile(jsonFilePath, { autosave: true });
    jsonFile.append(userData._id, userData);

    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);

      const file_path = path.join(fileStoragePath, file.name);

      await writeFile(file_path, buffer);
    }
    // step 4 ends

    /// step 5 starts
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
