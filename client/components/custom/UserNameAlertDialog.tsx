"use client";
import { space_grotesk } from "@/fonts";
import { cn } from "@/lib/utils";
import { Dispatch, SetStateAction, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { toast } from "sonner";
import { setDBUserData } from "@/db/files.db";
import { UserType } from "@/types/user.types";

export default function UserNameAlertDialog({
  openDialog,
  setOpenDialog,
  userData,
  formAction,
}: {
  formAction: () => void;
  userData: UserType;
  openDialog: boolean;
  setOpenDialog: Dispatch<SetStateAction<boolean>>;
}) {
  const [name, setName] = useState<string>("");

  function handleFormAction() {
    if (name == "") {
      toast.warning("Enter a valid name!");
      setOpenDialog(true);
    } else {
      setDBUserData({ ...userData, name });
      formAction();
      setOpenDialog(false);
    }
  }

  function dialogOpenChangeHandler(e: boolean) {
    setName("");
    setDBUserData({ ...userData, name: "" });
    setOpenDialog(false);
  }

  return (
    <AlertDialog
      onOpenChange={(e) => dialogOpenChangeHandler(e)}
      open={openDialog}
    >
      <AlertDialogPortal>
        <AlertDialogOverlay />
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className={cn(space_grotesk.className)}>
              Write your name
            </AlertDialogTitle>
            <AlertDialogDescription className={cn(space_grotesk.className)}>
              Your name is used to track your uploads.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            type="text"
            required
            autoFocus={openDialog}
          />
          <AlertDialogFooter className={cn(space_grotesk.className)}>
            <AlertDialogAction
              onClick={handleFormAction}
              className={cn(
                "bg-[#5f66f2] hover:bg-[#4049e5] border-2 border-black border-b-4 border-r-4 text-lg py-4 px-2 cursor-pointer",
                space_grotesk.className,
              )}
              asChild
            >
              <Button>send files</Button>
            </AlertDialogAction>
            <AlertDialogCancel
              className={cn(
                "bg-transparent border-none hover:bg-transparent dark:text-white hover:text-black text-black dark:bg-transparent text-lg py-4 px-2 mt-0.5 cursor-pointer",
              )}
              asChild
            >
              <Button>cancel</Button>
            </AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialogPortal>
    </AlertDialog>
  );
}
