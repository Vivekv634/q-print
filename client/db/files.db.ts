import { CustomFileBlob } from "@/app/page";
import { UserType } from "@/types/user.types";
import { openDB } from "idb";

const DB_NAME = "Q-PRINT";
const DB_VERSION = 1;
const USER_STORE = "USER STORE";
const FILES_STORE = "FILES STORE";
const FILE_SET = "FILE SET";

export async function _database() {
  const _db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(_db) {
      _db.createObjectStore(FILE_SET);
      _db.createObjectStore(USER_STORE);
      _db.createObjectStore(FILES_STORE);
    },
  });
  return _db;
}

// function to check if indexeddb is supported or not
export function indexeddb_supported() {
  return window.indexedDB;
}

// remove method for fileblobs
export async function emptyFileStore() {
  (await _database()).clear(FILES_STORE);
}

// set method for fileblobs
export async function setFileStore(files: CustomFileBlob[]) {
  (await _database()).put(FILES_STORE, files, 1);
}

// get method for fileblobs
export async function getFileStore() {
  return (await _database()).get(FILES_STORE, 1);
}

// set method for file_set
export async function setFileSet(file_set: string[]) {
  (await _database()).put(FILE_SET, file_set, 1);
}

// get method for file_set
export async function getFileSet() {
  return (await _database()).get(FILE_SET, 1);
}

// empty method for file_set
export async function emptyFileSet() {
  (await _database()).clear(FILE_SET);
}

// add records to the database
export async function setDBUserData(input_data: UserType) {
  return (await _database()).put(USER_STORE, input_data, 1);
}

// get method for userdata
export async function getDBUserData() {
  return (await _database()).get(USER_STORE, 1);
}

// empty method for userdata
export async function emptyDBUserData() {
  (await _database()).clear(USER_STORE);
}
