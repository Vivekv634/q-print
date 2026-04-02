import { CustomFileBlob } from "@/types/custom.types";
import { UserType } from "@/types/user.types";
import { openDB, IDBPDatabase } from "idb";

const DB_NAME = "Q-PRINT ACTIVITY";
const DB_VERSION = 1;
const USER_STORE = "ACTIVITY USER STORE";
const FILES_STORE = "ACTIVITY FILES STORE";

export interface CustomFileAcitvityObject {
  [key: string]: CustomFileBlob[];
}

export interface UserAcitvityObject {
  [key: string]: UserType;
}

export async function activityDatabase(): Promise<IDBPDatabase> {
  const _db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(_db) {
      _db.createObjectStore(USER_STORE);
      _db.createObjectStore(FILES_STORE);
    },
  });
  return _db;
}

// set method for fileblobs
export async function setActivityFileStore(
  files: CustomFileBlob[],
  user_id: string,
): Promise<void> {
  await (await activityDatabase()).put(FILES_STORE, files, user_id);
}

// get method for fileblobs by user user_id
export async function getActivityFileStore(
  user_id: string,
): Promise<CustomFileBlob[] | undefined> {
  return (await activityDatabase()).get(FILES_STORE, user_id);
}

// getall method for fileblobs for fetching all the fileblobs objects
export async function getAllActivityFileStore(): Promise<CustomFileBlob[][]> {
  return (await activityDatabase()).getAll(FILES_STORE);
}

// empty method for fileblobs
export async function emptyActivityFileStore(): Promise<void> {
  await (await activityDatabase()).clear(FILES_STORE);
}

// set method for userdata
export async function setActivityUserData(input_data: UserType): Promise<void> {
  await (await activityDatabase()).put(USER_STORE, input_data, input_data._id);
}

// get user record from the database by user user_id
export async function getActivityUserData(
  user_id: string,
): Promise<UserType | undefined> {
  return (await activityDatabase()).get(USER_STORE, user_id);
}

// getall method to fetch all userdata
export async function getAllActivityUserData(): Promise<UserType[]> {
  return (await activityDatabase()).getAll(USER_STORE);
}

// empty method for userdata
export async function emptyActivityUserData(): Promise<void> {
  await (await activityDatabase()).clear(USER_STORE);
}

// retrieve all data within single transactions per store to guarantee key-value consistency
export async function getAllData(): Promise<{
  fileObject: CustomFileAcitvityObject;
  userObject: UserAcitvityObject;
}> {
  const db = await activityDatabase();

  const userTx = db.transaction(USER_STORE, "readonly");
  const [userkey, uservalue] = await Promise.all([
    userTx.store.getAllKeys(),
    userTx.store.getAll(),
  ]);
  await userTx.done;

  const userObject: UserAcitvityObject = {};
  userkey.forEach((key, i) => {
    userObject[key as string] = uservalue[i];
  });

  const fileTx = db.transaction(FILES_STORE, "readonly");
  const [filekey, filevalue] = await Promise.all([
    fileTx.store.getAllKeys(),
    fileTx.store.getAll(),
  ]);
  await fileTx.done;

  const fileObject: CustomFileAcitvityObject = {};
  filekey.forEach((key, i) => {
    fileObject[key as string] = filevalue[i];
  });

  return { fileObject, userObject };
}
