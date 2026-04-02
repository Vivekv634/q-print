"use client";

import { space_grotesk, jetbrains_mono } from "@/fonts";
import { cn } from "@/lib/utils";
import { USER_ID_LENGTH } from "@/lib/constants";
import UserNameAlertDialog from "./UserNameAlertDialog";
import { Label } from "../ui/label";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { userSchema, UserType } from "@/types/user.types";
import { CustomFileBlob } from "@/types/custom.types";
import { FileDataType } from "@/types/filedata.types";
import { useState, Activity, useEffect, SetStateAction, Dispatch, useMemo } from "react";
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
import { UploadIcon } from "lucide-react";

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
  const [accordionDefaultValue, setAccordionDefaultValue] = useState<string[]>([]);
  const [openUserNameDialogState, setOpenUsernameDialogState] = useState<boolean>(false);
  const [costConfig, setCostConfig] = useState<{ color_per_page: number; bw_per_page: number } | null>(null);

  useEffect(() => {
    _database();
    getFileStore().then((res) => {
      if (res) setFiles(res as CustomFileBlob[]);
    });
    getDBUserData().then((res) => {
      if (res) setUserData(res as UserType);
    });
  }, []);

  useEffect(() => {
    fetch("/cost.json")
      .then((r) => r.json())
      .then((data) => setCostConfig(data))
      .catch(() => {});
  }, []);

  const totalCost = useMemo(() => {
    if (!costConfig || userData.filedataArray.length === 0) return null;
    return userData.filedataArray.reduce((sum, fd) => {
      const rate = fd.color_mode === "color" ? costConfig.color_per_page : costConfig.bw_per_page;
      return sum + (fd.page_count ?? 1) * fd.no_of_copies * rate;
    }, 0);
  }, [userData.filedataArray, costConfig]);

  async function handleFormSubmit() {
    if (!userData) return;
    if (userData.filedataArray.length == 0 || files.length == 0) {
      toast.warning("Please select atleast 1 PDF file.");
      return;
    }
    const formdata: FormData = new FormData();
    const dbUserData = (await getDBUserData()) as UserType | undefined;
    const updatedUserData: UserType = {
      ...userData,
      ...(dbUserData ?? {}),
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
    files.forEach((fileObj) => {
      const originalFile = fileObj.file;
      const newFileName = `${userData._id}_${userData.name}_${fileObj._id}_${originalFile.name}`;
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
      await setActivityUserData(responseBody.userData);
      await setActivityFileStore(files, responseBody.userData._id);
      await emptyDBUserData();
      await emptyFileStore();
      await emptyFileSet();
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
    await fileAddFeature({ input_files, setFiles, setUserData, files, userData });
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
      setAccordionDefaultValue(files.map((f) => f.file.name));
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
    <form onSubmit={(e) => e.preventDefault()} className="flex flex-col gap-4">

      {/* ── Upload drop zone — dot-grid paper aesthetic ── */}
      <div>
        <Label
          htmlFor="file_input"
          className={cn(
            "flex flex-col items-center justify-center gap-3",
            "border-2 border-dashed border-foreground rounded-none",
            "py-10 px-4 cursor-pointer dot-bg",
            "transition-colors duration-150",
            "hover:bg-primary/20",
            space_grotesk.className,
          )}
        >
          <UploadIcon className="h-8 w-8" strokeWidth={2.5} />
          <span className={cn("font-black text-sm tracking-[0.2em] uppercase")}>
            Drop PDFs here
          </span>
          <span className={cn("nb-tag text-muted-foreground", jetbrains_mono.className)}>
            Multiple files supported · PDF only
          </span>
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

      {/* ── Cost estimate — yellow left-bar accent ── */}
      {totalCost !== null && files.length > 0 && (
        <div
          className={cn(
            "flex justify-between items-center px-4 py-3",
            "border-2 border-foreground border-l-[6px]",
            "rounded-none bg-card",
            space_grotesk.className,
          )}
          style={{
            borderLeftColor: "#FFE500",
            boxShadow: "var(--nb-shadow-xs)",
          }}
        >
          <span className={cn("nb-tag text-muted-foreground", jetbrains_mono.className)}>
            Estimated Cost
          </span>
          <span className="text-2xl font-black">₹{totalCost.toFixed(2)}</span>
        </div>
      )}

      {/* ── Actions row ── */}
      <div className={cn("w-full flex justify-end gap-2", space_grotesk.className)}>
        <UserNameAlertDialog
          formAction={handleFormSubmit}
          userData={userData}
          setOpenDialog={setOpenUsernameDialogState}
          openDialog={openUserNameDialogState}
        />
        <Button
          onClick={nameDialogOpenerHandler}
          className={cn(
            "cursor-pointer font-black text-primary-foreground tracking-widest",
            "bg-primary border-2 border-foreground rounded-none px-7 py-2.5 nb-press",
          )}
          style={{ boxShadow: "var(--nb-shadow)" }}
        >
          SEND FILES
        </Button>
      </div>

      {/* Separator */}
      <div className="nb-separator w-full" />

      {/* ── File list section ── */}
      <section>
        <Activity mode={files.length == 0 ? "hidden" : "visible"}>
          <div className="flex w-full justify-between items-center mb-3">
            {/* File count badge */}
            <span
              className={cn(
                "nb-tag px-2 py-1 border-2 border-foreground bg-secondary text-foreground",
                jetbrains_mono.className,
              )}
            >
              {files.length} file{files.length !== 1 ? "s" : ""} queued
            </span>
            <Button
              onClick={handleAccordionCollapsibleStates}
              className={cn(
                "bg-transparent border-none underline font-bold text-sm cursor-pointer",
                space_grotesk.className,
              )}
              type="button"
            >
              {accordionDefaultValue.length !== userData.filedataArray.length
                ? "open all"
                : "collapse all"}
            </Button>
          </div>
        </Activity>
        <Activity mode={files.length == 0 ? "hidden" : "visible"}>
          <Accordion
            type="multiple"
            className="flex flex-col gap-3"
            value={accordionDefaultValue}
            onValueChange={setAccordionDefaultValue}
          >
            {files.map((file_object, i) => (
              <FileDetailAccordion
                key={i}
                userData={userData}
                file={file_object}
                bufferFileDeleteHandler={bufferFileDeleteHandler}
                fileDataUpdateHandler={fileDataUpdateHandler}
              />
            ))}
          </Accordion>
        </Activity>
        <Activity mode={files.length != 0 ? "hidden" : "visible"}>
          <p
            className={cn(
              "text-center nb-tag py-6 text-muted-foreground",
              jetbrains_mono.className,
            )}
          >
            No files uploaded yet.
          </p>
        </Activity>
      </section>
    </form>
  );
}
