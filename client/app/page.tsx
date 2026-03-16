"use client";

import { space_grotesk } from "@/fonts";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";
import { Toaster } from "sonner";
import HeadingSection from "@/components/custom/HeadingSection";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import FileUploadTabSection from "@/components/custom/FileUploadTabSection";
import ActivityTabSection from "@/components/custom/ActivityTabSection";
import { useState } from "react";

export interface CustomFileBlob {
  _id: string;
  file: File;
}

export default function Page() {
  const [tabValue, setTabValue] = useState<"upload" | "activity">("upload");
  const { theme } = useTheme();

  return (
    <main className="container mx-auto lg:max-w-1/2 w-full">
      <Toaster
        position="top-center"
        richColors={true}
        theme={theme == "light" ? "light" : "dark"}
        swipeDirections={["left", "right", "top"]}
      />
      {/* The main box */}
      <HeadingSection />

      {/* file upload section */}
      <section className="m-3 border-foreground border-2 p-5 rounded-2xl bg-background text-foreground border-b-[5px] border-r-[5px]">
        <Tabs
          defaultValue="upload"
          value={tabValue}
          onValueChange={(e) =>
            setTabValue(e == "upload" ? "upload" : "activity")
          }
        >
          <TabsList className="w-full mb-3">
            <TabsTrigger
              value="upload"
              className={cn(space_grotesk.className, "cursor-pointer")}
            >
              Upload
            </TabsTrigger>
            <TabsTrigger
              value="activity"
              className={cn(space_grotesk.className, "cursor-pointer")}
            >
              Activity
            </TabsTrigger>
          </TabsList>
          <TabsContent value="upload">
            <FileUploadTabSection setTabValue={setTabValue} />
          </TabsContent>
          <TabsContent value="activity">
            <ActivityTabSection />
          </TabsContent>
        </Tabs>
      </section>
    </main>
  );
}
