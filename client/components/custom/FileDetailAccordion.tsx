"use client";

import { space_grotesk, jetbrains_mono } from "@/fonts";
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
    page_count: 1,
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
    /*
     * Each file accordion item = a "paper" in the stack.
     * Lime left accent bar (6px) marks it as a file item.
     * Sharp corners throughout.
     */
    <AccordionItem
      value={_file.name}
      className={cn(
        "border-2 border-foreground border-l-[6px] rounded-none px-3 py-2 font-medium",
        space_grotesk.className,
      )}
      style={{
        borderLeftColor: "#BEFF72",
        boxShadow: "var(--nb-shadow-xs)",
      }}
    >
      {/* Header row: filename + delete */}
      <div className="flex justify-between w-full items-center gap-2">
        <AccordionTrigger
          className="cursor-pointer font-semibold text-[14px] flex-1 min-w-0 text-left"
        >
          <span className="truncate block">{_file.name}</span>
        </AccordionTrigger>
        <button
          type="button"
          className={cn(
            "shrink-0 border-2 border-foreground rounded-none p-1.5",
            "bg-destructive text-destructive-foreground cursor-pointer nb-press",
          )}
          style={{ boxShadow: "var(--nb-shadow-xs)" }}
          onClick={() => bufferFileDeleteHandler(_file.name)}
          title="Remove file"
        >
          <Trash className="h-3.5 w-3.5" />
        </button>
      </div>

      <AccordionContent className="mt-4">
        {/* Settings grid */}
        <div className="flex flex-col gap-3.5">

          {/* Copies stepper — full-width row */}
          <div className="flex justify-between items-center">
            <Label className={cn("text-sm font-bold", jetbrains_mono.className)}>
              COPIES
            </Label>
            <ButtonGroup>
              <Button
                variant="outline"
                onClick={() => {
                  const newCopies = fileData.no_of_copies - 1 <= 1 ? 1 : fileData.no_of_copies - 1;
                  const updatedFileData = { ...fileData, no_of_copies: newCopies };
                  setFileData(updatedFileData);
                  fileDataUpdateHandler({ file_id: file._id, file_data: updatedFileData });
                }}
                disabled={fileData.no_of_copies <= 1}
                size="icon"
                className="rounded-none border-2 border-foreground"
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
                  "max-w-14 px-0 mx-auto text-center rounded-none border-2 border-foreground font-bold",
                  buttonVariants({ variant: "outline" }),
                )}
              />
              <Button
                variant="outline"
                disabled={fileData.no_of_copies >= 20}
                onClick={() => {
                  const newCopies = fileData.no_of_copies + 1 >= 20 ? 20 : fileData.no_of_copies + 1;
                  const updatedFileData = { ...fileData, no_of_copies: newCopies };
                  setFileData(updatedFileData);
                  fileDataUpdateHandler({ file_id: file._id, file_data: updatedFileData });
                }}
                size="icon"
                className="rounded-none border-2 border-foreground"
              >
                <PlusIcon />
              </Button>
            </ButtonGroup>
          </div>

          {/* Print settings — compact rows */}
          {[
            {
              label: "MODE",
              value: fileData.color_mode,
              onChange: (e: string) =>
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: { ...fileData, color_mode: e as "color" | "black_&_white" },
                }),
              options: [
                { value: "black_&_white", label: "B & W" },
                { value: "color", label: "Color" },
              ],
            },
            {
              label: "LAYOUT",
              value: fileData.layout,
              onChange: (e: string) =>
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: { ...fileData, layout: e as "portrait" | "landscape" },
                }),
              options: [
                { value: "portrait", label: "Portrait" },
                { value: "landscape", label: "Landscape" },
              ],
            },
            {
              label: "MARGINS",
              value: fileData.margins,
              onChange: (e: string) =>
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: { ...fileData, margins: e as "default" | "minimal" | "none" },
                }),
              options: [
                { value: "default", label: "Default" },
                { value: "minimal", label: "Minimal" },
                { value: "none", label: "None" },
              ],
            },
            {
              label: "PAPER",
              value: fileData.paper_size,
              onChange: (e: string) =>
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: {
                    ...fileData,
                    paper_size: e as "letter" | "legal" | "tabloid" | "a0" | "a1" | "a2" | "a3" | "a4" | "a5",
                  },
                }),
              options: [
                { value: "letter", label: "Letter" },
                { value: "legal", label: "Legal" },
                { value: "tabloid", label: "Tabloid" },
                { value: "a0", label: "A0" },
                { value: "a1", label: "A1" },
                { value: "a2", label: "A2" },
                { value: "a3", label: "A3" },
                { value: "a4", label: "A4" },
                { value: "a5", label: "A5" },
              ],
            },
            {
              label: "BG GRAPHICS",
              value: fileData.background_graphics ? "yes" : "no",
              onChange: (e: string) =>
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: { ...fileData, background_graphics: e === "yes" },
                }),
              options: [
                { value: "yes", label: "Yes" },
                { value: "no", label: "No" },
              ],
            },
            {
              label: "HDR / FTR",
              value: fileData.headers_footers ? "yes" : "no",
              onChange: (e: string) =>
                fileDataUpdateHandler({
                  file_id: file._id,
                  file_data: { ...fileData, headers_footers: e === "yes" },
                }),
              options: [
                { value: "yes", label: "Yes" },
                { value: "no", label: "No" },
              ],
            },
          ].map(({ label, value, onChange, options }) => (
            <div key={label} className="flex justify-between items-center">
              <Label className={cn("text-xs font-bold", jetbrains_mono.className)}>
                {label}
              </Label>
              <Select value={value} onValueChange={onChange}>
                <SelectTrigger className="w-32 rounded-none border-2 border-foreground font-semibold text-sm h-8">
                  <SelectValue placeholder="select" />
                </SelectTrigger>
                <SelectContent
                  position="popper"
                  side="bottom"
                  align="end"
                  className="rounded-none border-2 border-foreground"
                >
                  {options.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="rounded-none font-medium">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
