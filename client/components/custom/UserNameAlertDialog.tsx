"use client";
import { space_grotesk, jetbrains_mono } from "@/fonts";
import { cn } from "@/lib/utils";
import { Dispatch, SetStateAction, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
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

  function dialogOpenChangeHandler(_e: boolean) {
    setName("");
    setOpenDialog(false);
  }

  return (
    <AlertDialog
      onOpenChange={(e) => dialogOpenChangeHandler(e)}
      open={openDialog}
    >
      <AlertDialogPortal>
        <AlertDialogOverlay />
        <AlertDialogContent
          className={cn(
            "border-2 border-foreground rounded-none p-0 overflow-hidden",
            space_grotesk.className,
          )}
          style={{ boxShadow: "var(--nb-shadow-lg)" }}
        >
          {/* Yellow accent header bar — full width strip */}
          <div className="bg-primary border-b-2 border-foreground px-5 py-4">
            <AlertDialogTitle className="font-black text-xl text-primary-foreground leading-tight">
              Who&apos;s printing?
            </AlertDialogTitle>
            <AlertDialogDescription
              className={cn("nb-tag text-primary-foreground/70 mt-1", jetbrains_mono.className)}
            >
              Your name identifies your job in the queue.
            </AlertDialogDescription>
          </div>

          {/* Form body */}
          <div className="px-5 py-4 flex flex-col gap-4">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              type="text"
              required
              autoFocus={openDialog}
              placeholder="Enter your name"
              className={cn(
                "rounded-none border-2 border-foreground font-bold text-base",
                "focus-visible:ring-0 focus-visible:border-primary",
                space_grotesk.className,
              )}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleFormAction();
              }}
            />

            <AlertDialogFooter className="gap-2 flex-row sm:flex-row">
              {/* Primary: yellow, shadow-collapse */}
              <AlertDialogAction
                onClick={handleFormAction}
                className={cn(
                  "flex-1 bg-primary text-primary-foreground border-2 border-foreground rounded-none",
                  "font-black tracking-widest nb-press cursor-pointer",
                  space_grotesk.className,
                )}
                style={{ boxShadow: "var(--nb-shadow-sm)" }}
                asChild
              >
                <Button>SEND FILES</Button>
              </AlertDialogAction>

              {/* Cancel: outlined, shadow-collapse */}
              <AlertDialogCancel
                className={cn(
                  "flex-1 bg-background text-foreground border-2 border-foreground rounded-none",
                  "font-bold nb-press cursor-pointer mt-0",
                  space_grotesk.className,
                )}
                style={{ boxShadow: "var(--nb-shadow-sm)" }}
                asChild
              >
                <Button>Cancel</Button>
              </AlertDialogCancel>
            </AlertDialogFooter>
          </div>
        </AlertDialogContent>
      </AlertDialogPortal>
    </AlertDialog>
  );
}
