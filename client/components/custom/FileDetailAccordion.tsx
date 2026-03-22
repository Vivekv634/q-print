"use client";

import { space_grotesk } from "@/fonts";
import { cn } from "@/lib/utils";
import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import { MinusIcon, PlusIcon, Trash } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Label } from "../ui/label";
import { Input } from "../ui/input";
import { CustomFileBlob } from "@/app/page";
import { UserType } from "@/types/user.types";
import { useEffect, useState } from "react";
import { FileDataType } from "@/types/filedata.types";
import { ButtonGroup } from "../ui/button-group";
import { Button, buttonVariants } from "../ui/button";

interface FileDetaileAccordionProps {
  file: CustomFileBlob;
  bufferFileDeleteHandler(file_name: string): void;
  fileDataUpdateHandler({
    file_data,
    file_id,
  }: {
    file_id: string;
    file_data: FileDataType;
  }): void;
  userData: UserType;
}

export default function FileDetailAccordion({
  file,
  bufferFileDeleteHandler,
  userData,
  fileDataUpdateHandler,
}: FileDetaileAccordionProps) {
  const _file = file.file;
  const [fileData, setFileData] = useState<FileDataType>({
    _file_id: file._id,
    background_graphics: false,
    color_mode: "black_&_white",
    file_name: _file.name,
    headers_footers: false,
    layout: "portrait",
    margins: "default",
    no_of_copies: 1,
    paper_size: "a4",
  });

  useEffect(() => {
    const existingData = userData.filedataArray.find(
      (FD) => FD._file_id === file._id,
    );
    if (existingData) {
      setFileData(existingData);
    }
  }, [userData.filedataArray, file._id]);

  return (
    <AccordionItem
      value={_file.name}
      className={cn(
        "border-2 rounded-lg border-r-4 border-b-4 px-3 py-2 font-medium",
        space_grotesk.className,
      )}
    >
      <div className="flex justify-between w-full items-center">
        <AccordionTrigger className="cursor-pointer font-medium text-[17px] flex items-center gap-2">
          {_file.name}
        </AccordionTrigger>
        <div
          className="rounded-full bg-red-200 dark:bg-red-100 cursor-pointer hover:bg-red-300 dark:hover:bg-red-300 p-2"
          onClick={() => bufferFileDeleteHandler(_file.name)}
        >
          <Trash className="text-red-700 dark:text-red-500 h-5 w-5" />
        </div>
      </div>
      <AccordionContent className="flex flex-col gap-5 mt-3">
        {/* No. of copies */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">No. of copies</Label>
          <ButtonGroup>
            <Button
              variant={"outline"}
              onClick={() => {
                const newCopies =
                  fileData.no_of_copies - 1 <= 1
                    ? 1
                    : fileData.no_of_copies - 1;
                const updatedFileData = {
                  ...fileData,
                  no_of_copies: newCopies,
                };
                setFileData(updatedFileData);
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: updatedFileData,
                });
              }}
              disabled={fileData.no_of_copies <= 1}
              size={"icon"}
            >
              <MinusIcon />
            </Button>
            <Input
              min={1}
              max={20}
              value={fileData.no_of_copies}
              readOnly
              type="number"
              className={cn(
                "max-w-14 px-0 mx-auto text-center",
                buttonVariants({ variant: "outline" }),
              )}
            />
            <Button
              variant={"outline"}
              disabled={fileData.no_of_copies >= 20}
              onClick={() => {
                const newCopies =
                  fileData.no_of_copies + 1 >= 20
                    ? 20
                    : fileData.no_of_copies + 1;
                const updatedFileData = {
                  ...fileData,
                  no_of_copies: newCopies,
                };
                setFileData(updatedFileData);
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: updatedFileData,
                });
              }}
              size={"icon"}
            >
              <PlusIcon />
            </Button>
          </ButtonGroup>
        </div>

        {/* print mode */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">Mode</Label>
          <Select
            defaultValue="black_&_white"
            name=""
            value={fileData.color_mode}
            onValueChange={(e) =>
              fileDataUpdateHandler({
                file_id: file._id,
                file_data: {
                  ...fileData,
                  color_mode: e as "color" | "black_&_white",
                },
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="select" />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="end">
              <SelectItem value="black_&_white">Black & White</SelectItem>
              <SelectItem value="color">Color</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* layout */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">Layout</Label>
          <Select
            defaultValue="portrait"
            value={fileData.layout}
            onValueChange={(e) =>
              fileDataUpdateHandler({
                file_id: file._id,
                file_data: {
                  ...fileData,
                  layout: e as "portrait" | "landscape",
                },
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="select" />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="end">
              <SelectItem value="portrait">Portraint</SelectItem>
              <SelectItem value="landscape">Landscape</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* margins */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">Margins</Label>
          <Select
            defaultValue="default"
            value={fileData.margins}
            onValueChange={(e) =>
              fileDataUpdateHandler({
                file_id: file._id,
                file_data: {
                  ...fileData,
                  margins: e as "default" | "minimal" | "none",
                },
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="select" />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="end">
              <SelectItem value="default">Default</SelectItem>
              <SelectItem value="minimal">Minimal</SelectItem>
              <SelectItem value="none">None</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* paper size */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">Paper size</Label>
          <Select
            defaultValue="a4"
            value={fileData.paper_size}
            onValueChange={(e) =>
              fileDataUpdateHandler({
                file_id: file._id,
                file_data: {
                  ...fileData,
                  paper_size: e as
                    | "letter"
                    | "legal"
                    | "tabloid"
                    | "a0"
                    | "a1"
                    | "a2"
                    | "a3"
                    | "a4"
                    | "a5",
                },
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="select" />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="end">
              <SelectItem value="letter">Letter</SelectItem>
              <SelectItem value="legal">Legal</SelectItem>
              <SelectItem value="tabloid">Tabloid</SelectItem>
              <SelectItem value="a0">A0</SelectItem>
              <SelectItem value="a1">A1</SelectItem>
              <SelectItem value="a2">A2</SelectItem>
              <SelectItem value="a3">A3</SelectItem>
              <SelectItem value="a4">A4</SelectItem>
              <SelectItem value="a5">A5</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* background_graphics */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">Background Graphics</Label>
          <Select
            defaultValue="no"
            value={fileData.background_graphics ? "yes" : "no"}
            onValueChange={(e) =>
              fileDataUpdateHandler({
                file_id: file._id,
                file_data: {
                  ...fileData,
                  background_graphics: e == "yes",
                },
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="select" />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="end">
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* headers & footers */}
        <div className="flex justify-between">
          <Label className="text-xl font-semibold">Headers & Footers</Label>
          <Select
            defaultValue="no"
            value={fileData.headers_footers ? "yes" : "no"}
            onValueChange={(e) =>
              fileDataUpdateHandler({
                file_id: file._id,
                file_data: {
                  ...fileData,
                  headers_footers: e == "yes",
                },
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="select" />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="end">
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
