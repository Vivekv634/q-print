import z from "zod";
import { filedataSchema } from "./filedata.types";

export const userSchema = z.object({
  _id: z.string(),
  name: z.string().min(1),
  timestamp: z.number(),
  position: z.number().min(1).nullable(),
  filedataArray: z.array(filedataSchema).min(1),
  estimated_time_of_print: z.number().nullable(),
  completed: z.boolean().default(false),
});

export type UserType = z.infer<typeof userSchema>;
