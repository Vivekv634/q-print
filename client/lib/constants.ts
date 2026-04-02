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

export const printQueuePath = path.join(process.cwd(), "data", "print_queue.json");
export const shopConfigPath = path.join(process.cwd(), "shop_config.json");
export const discoveredPeersPath = path.join(process.cwd(), "data", "discovered_peers.json");
