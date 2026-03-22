"use client";

import { space_grotesk } from "@/fonts";
import { cn } from "@/lib/utils";
import { USER_ID_LENGTH } from "@/lib/constants";
import UserNameAlertDialog from "./UserNameAlertDialog";
import { Label } from "../ui/label";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { userSchema, UserType } from "@/types/user.types";
import { CustomFileBlob } from "@/app/page";
import { FileDataType } from "@/types/filedata.types";
import { useState, Activity, useEffect, SetStateAction, Dispatch } from "react";
import FileDetailAccordion from "./FileDetailAccordion";
import { Accordion } from "../ui/accordion";
import { uid } from "uid";
import {
  _database,
  emptyDBUserData,
  emptyFileSet,
  emptyFileStore,
  getDBUserData,
  getFileStore,
} from "@/db/files.db";
import {
  fileAddFeature,
  FileDataUpdateHandler,
  fileRemoveFeature,
} from "@/db/features/file.features";
import { toast } from "sonner";
import { setActivityFileStore, setActivityUserData } from "@/db/activity.db";

const userTemplate: UserType = {
  _id: uid(USER_ID_LENGTH),
  estimated_time_of_print: 0,
  name: "",
  completed: false,
  filedataArray: [],
  position: 1,
  timestamp: new Date().getTime(),
};

interface FileUploadSectionInterface {
  setTabValue: Dispatch<SetStateAction<"upload" | "activity">>;
}

export default function FileUploadSection({
  setTabValue,
}: FileUploadSectionInterface) {
  const [userData, setUserData] = useState<UserType>(userTemplate);
  const [files, setFiles] = useState<CustomFileBlob[]>([]);
  const [accordionDefaultValue, setAccordionDefaultValue] = useState<string[]>(
    [],
  );
  const [openUserNameDialogState, setOpenUsernameDialogState] =
    useState<boolean>(false);

  useEffect(() => {
    _database();
    getFileStore().then((res) => {
      if (res) {
        setFiles(res as CustomFileBlob[]);
      }
    });
    getDBUserData().then((res) => {
      if (res) {
        setUserData(res as UserType);
      }
    });
  }, []);

  async function handleFormSubmit() {
    if (!userData) return;
    if (userData.filedataArray.length == 0 || files.length == 0) {
      toast.warning("Please select atleast 1 PDF file.");
      return;
    }
    const formdata: FormData = new FormData();
    const dbUserData = (await getDBUserData()) as UserType;
    const updatedUserData = {
      ...userData,
      ...dbUserData,
      timestamp: new Date().getTime(),
    };
    const parsedUpdatedUserData = userSchema.safeParse(updatedUserData);
    if (!parsedUpdatedUserData.success) {
      console.log(parsedUpdatedUserData.error);
      toast.error("Getting error while parsing the userData data");
      return;
    }
    setUserData(updatedUserData);
    formdata.append("userData", JSON.stringify(updatedUserData));
    // Rename and append files with userData ID prefix
    files.forEach((fileObj) => {
      const originalFile = fileObj.file;
      const newFileName = `${userData._id}_${userData.name}_${fileObj._id}_${originalFile.name}`;
      // Create a new File object with the new name
      const renamedFile = new File([originalFile], newFileName, {
        type: originalFile.type,
        lastModified: originalFile.lastModified,
      });
      formdata.append("files", renamedFile);
    });
    try {
      const response = await fetch(`/api/jobs/upload`, {
        method: "POST",
        body: formdata,
        credentials: "same-origin",
      });
      if (!response.ok) {
        toast.error("Facing some error, try again.");
        return;
      }

      const responseBody = (await response.json()) as {
        message: string;
        fileCount: number;
        userData: UserType;
      };

      // append userdata store in activity database by their id as a key
      setActivityUserData(responseBody.userData);
      setActivityFileStore(files, responseBody.userData._id);

      // remove all data from the file upload section
      emptyDBUserData();
      emptyFileStore();
      emptyFileSet();
      setFiles([]);
      setUserData(userTemplate);

      toast.success(`${responseBody.fileCount} file(s) upload received!`);
      setTabValue("activity");
    } catch (error) {
      console.error(error);
      toast.error("Error uploading files. Try again!");
    }
  }

  async function handle_add_file(input_files: FileList | null) {
    await fileAddFeature({
      input_files,
      setFiles,
      setUserData,
      files,
      userData,
    });
  }

  async function bufferFileDeleteHandler(file_name: string) {
    await fileRemoveFeature({ file_name, userData, setFiles, setUserData });
  }

  function nameDialogOpenerHandler() {
    if (files.length == 0) {
      toast.warning("Please select atleast 1 PDF file.");
      return;
    }
    setOpenUsernameDialogState(true);
  }

  function handleAccordionCollapsibleStates() {
    if (accordionDefaultValue.length == 0) {
      const filename_mapper = files.map((f) => f.file.name);
      setAccordionDefaultValue(filename_mapper);
    } else {
      setAccordionDefaultValue([]);
    }
  }

  async function fileDataUpdateHandler({
    file_id,
    file_data,
  }: {
    file_id: string;
    file_data: FileDataType;
  }) {
    await FileDataUpdateHandler({ file_data, file_id, userData, setUserData });
  }

  return (
    <form onSubmit={(e) => e.preventDefault()} className="flex flex-col gap-3">
      <div>
        <Label
          className={cn(
            "outline-dashed outline-[3px] cursor-pointer hover:bg-[#d3d3d3] rounded-2xl py-5 px-3 bg-[#e9e9e9] dark:bg-[#262626] font-bold",
            space_grotesk.className,
          )}
          htmlFor="file_input"
        >
          <p className="text-center w-full flex flex-col items-center">
            Click here to upload files
          </p>
        </Label>
        <Input
          autoFocus
          type="file"
          multiple
          onChange={(e) => handle_add_file(e.target.files)}
          required
          accept=".pdf"
          id="file_input"
          name="file_input"
          className="hidden"
        />
      </div>

      <div
        className={cn(
          "w-full tracking-wide flex justify-end gap-2",
          space_grotesk.className,
        )}
      >
        <UserNameAlertDialog
          formAction={handleFormSubmit}
          userData={userData}
          setOpenDialog={setOpenUsernameDialogState}
          openDialog={openUserNameDialogState}
        />
        <Button
          onClick={nameDialogOpenerHandler}
          className="text-center w-fit cursor-pointer font-semibold text-foreground dark:text-background hover:bg-[#ffa310] active:bg-[#f09400] bg-[#ffad2a] border-2 border-black border-b-4 border-r-4 rounded-xl py-5 px-7"
        >
          Send Files
        </Button>
      </div>

      <hr className="w-full border-2" />

      {/* file details display section */}
      <section>
        <Activity mode={files.length == 0 ? "hidden" : "visible"}>
          <div className="flex w-full justify-end mb-2">
            <Button
              onClick={handleAccordionCollapsibleStates}
              className={cn(
                "underline cursor-pointer bg-transparent border-none text-accent-foreground text-lg",
                space_grotesk.className,
              )}
              type="button"
            >
              {accordionDefaultValue.length != userData.filedataArray.length
                ? "open all"
                : "collapse all"}
            </Button>
          </div>
        </Activity>
        <Activity mode={files.length == 0 ? "hidden" : "visible"}>
          <Accordion
            type="multiple"
            className="gap-2"
            value={accordionDefaultValue}
            onValueChange={setAccordionDefaultValue}
          >
            {files.map((file_object, i) => {
              return (
                <FileDetailAccordion
                  key={i}
                  userData={userData}
                  file={file_object}
                  bufferFileDeleteHandler={bufferFileDeleteHandler}
                  fileDataUpdateHandler={fileDataUpdateHandler}
                />
              );
            })}
          </Accordion>
        </Activity>
        <Activity mode={files.length != 0 ? "hidden" : "visible"}>
          <div
            className={cn("text-center font-medium", space_grotesk.className)}
          >
            No files uploaded yet.
          </div>
        </Activity>
      </section>
    </form>
  );
}
