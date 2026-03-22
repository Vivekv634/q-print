import path from "path";

const JSON_FILE_NAME = "user_records.json";
const FILE_STORAGE_NAME = "print_job_file_storage";

export const jsonFilePath = path.join(process.cwd(), "data", JSON_FILE_NAME);
export const fileStoragePath = path.join(
  process.cwd(),
  "data",
  FILE_STORAGE_NAME,
);

export const USER_ID_LENGTH = 11;
export const FILE_ID_LENGTH = 7;
