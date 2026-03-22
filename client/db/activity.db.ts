import { CustomFileBlob } from "@/app/page";
import { UserType } from "@/types/user.types";
import { openDB } from "idb";

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

export async function activityDatabase() {
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
) {
  (await activityDatabase()).put(FILES_STORE, files, user_id);
}

// get method for fileblobs by user user_id
export async function getActivityFileStore(user_id: string) {
  return (await activityDatabase()).get(FILES_STORE, user_id);
}

// getall method for fileblobs for fetching all the fileblobs objects
export async function getAllActivityFileStore() {
  return (await activityDatabase()).getAll(FILES_STORE);
}

// empty method for fileblobs
export async function emptyActivityFileStore() {
  (await activityDatabase()).clear(FILES_STORE);
}

// set method for userdata
export async function setActivityUserData(input_data: UserType) {
  (await activityDatabase()).put(USER_STORE, input_data, input_data._id);
}

// get user record from the database by user user_id
export async function getActivityUserData(user_id: string) {
  return (await activityDatabase()).get(USER_STORE, user_id);
}

// getall method to fetch all userdata
export async function getAllActivityUserData() {
  return (await activityDatabase()).getAll(USER_STORE);
}

// empty method for userdata
export async function emptyActivityUserData() {
  (await activityDatabase()).clear(USER_STORE);
}

// retrive all data
export async function getAllData() {
  const [userkey, uservalue] = await Promise.all([
    (await activityDatabase()).getAllKeys(USER_STORE),
    (await activityDatabase()).getAll(USER_STORE),
  ]);
  const userObject: UserAcitvityObject = {};
  userkey.forEach((key, i) => {
    userObject[key as string] = uservalue[i];
  });

  const [filekey, filevalue] = await Promise.all([
    (await activityDatabase()).getAllKeys(FILES_STORE),
    (await activityDatabase()).getAll(FILES_STORE),
  ]);

  const fileObject: CustomFileAcitvityObject = {};
  filekey.forEach((key, i) => {
    fileObject[key as string] = filevalue[i];
  });
  return { fileObject, userObject };
}
