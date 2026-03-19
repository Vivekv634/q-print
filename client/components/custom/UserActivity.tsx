"use client";
import { UserType } from "@/types/user.types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { cn } from "@/lib/utils";
import { space_grotesk } from "@/fonts";
import { Separator } from "../ui/separator";

interface UserAcitvityInterface {
  userData: UserType;
}

export default function UserAcitvity({ userData }: UserAcitvityInterface) {
  if (!userData) return;
  return (
    <Card
      id={userData._id}
      className="border-2 rounded-lg border-r-4 border-b-4 font-medium"
    >
      <CardContent>
        <CardHeader>
          <CardTitle
            className={cn(space_grotesk.className, "flex justify-between")}
          >
            <p className="text-2xl font-semibold">{userData.name}</p>
            <h3 className="rounded-full bg-accent flex items-center justify-center text-lg px-3">
              {userData.position}
            </h3>
          </CardTitle>
          <CardDescription>
            <p>
              {new Date(userData.timestamp).toLocaleString("en-IN", {
                hourCycle: "h12",
              })}
            </p>
          </CardDescription>
        </CardHeader>
        <Separator className="my-2" />
        <p className="flex justify-end text-accent-foreground/40">
          User ID: {userData._id}
        </p>
      </CardContent>
    </Card>
  );
}
