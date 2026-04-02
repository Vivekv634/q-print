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

      <HeadingSection />

      {/* Main panel */}
      <section className="m-3 nb-card p-5">
        <Tabs
          defaultValue="upload"
          value={tabValue}
          onValueChange={(e) =>
            setTabValue(e == "upload" ? "upload" : "activity")
          }
        >
          {/*
           * Physical toggle tab switcher:
           * - Container has the offset shadow
           * - Active tab = filled + no shadow on the tab itself (looks "pressed in")
           * - Inactive tab = outlined, has slight raised appearance
           */}
          <TabsList
            className="w-full mb-6 h-auto p-0 gap-0 bg-transparent border-2 border-foreground rounded-none overflow-hidden"
            style={{ boxShadow: "var(--nb-shadow-sm)" }}
          >
            <TabsTrigger
              value="upload"
              className={cn(
                space_grotesk.className,
                "cursor-pointer flex-1 rounded-none py-3 font-black text-sm",
                "border-r-2 border-foreground",
                "transition-all duration-100",
                /* Active = yellow fill, translate down-right (pressed) */
                "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground",
                "data-[state=active]:translate-x-[2px] data-[state=active]:translate-y-[2px]",
                /* Inactive = transparent bg */
                "data-[state=inactive]:bg-transparent data-[state=inactive]:text-muted-foreground",
                "data-[state=inactive]:hover:bg-muted data-[state=inactive]:hover:text-foreground",
              )}
            >
              <span className="tracking-widest">UPLOAD</span>
            </TabsTrigger>
            <TabsTrigger
              value="activity"
              className={cn(
                space_grotesk.className,
                "cursor-pointer flex-1 rounded-none py-3 font-black text-sm",
                "transition-all duration-100",
                /* Active = teal fill, pressed */
                "data-[state=active]:bg-accent data-[state=active]:text-accent-foreground",
                "data-[state=active]:translate-x-[2px] data-[state=active]:translate-y-[2px]",
                /* Inactive = transparent bg */
                "data-[state=inactive]:bg-transparent data-[state=inactive]:text-muted-foreground",
                "data-[state=inactive]:hover:bg-muted data-[state=inactive]:hover:text-foreground",
              )}
            >
              <span className="tracking-widest">ACTIVITY</span>
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
