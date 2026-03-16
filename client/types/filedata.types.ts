import z from "zod";

export interface FileInterface {
  _id: string;
  file_name: string;
}

export const filedataSchema = z.object({
  _file_id: z.string(),
  file_name: z.string(),
  no_of_copies: z.number().min(1),
  color_mode: z.enum(["color", "black_&_white"]),
  layout: z.enum(["landscape", "portrait"]).default("portrait"),
  paper_size: z
    .enum(["a0", "a1", "a2", "a3", "a4", "a5", "letter", "legal", "tabloid"])
    .default("a4"),
  background_graphics: z.boolean().default(false),
  headers_footers: z.boolean().default(false),
  margins: z.enum(["none", "minimal", "default"]).default("default"),
});

export type FileDataType = z.infer<typeof filedataSchema>;
