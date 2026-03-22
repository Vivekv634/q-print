import { CustomFileBlob } from "@/app/page";
import { Dispatch, SetStateAction } from "react";
import { UserType } from "@/types/user.types";
import {
  getFileSet,
  setFileSet,
  setFileStore,
  setDBUserData,
  getFileStore,
} from "../files.db";
import { uid } from "uid";
import { FileDataType } from "@/types/filedata.types";
import { FILE_ID_LENGTH } from "@/lib/constants";

interface fileAddFeatureInterface {
  userData: UserType;
  files: CustomFileBlob[];
  input_files: FileList | null;
  setUserData: Dispatch<SetStateAction<UserType>>;
  setFiles: Dispatch<SetStateAction<CustomFileBlob[]>>;
}

export async function fileAddFeature({
  setFiles,
  userData,
  input_files,
  setUserData,
  files,
}: fileAddFeatureInterface) {
  /*
   This database feature will add a new file blob to the indexeddb only when it has unique name.

   steps:
   1. first, fetch the file_set for unique name identification.
   2. run a loop to filter the input_files with the help of file_set, bind an uid to the filtered files alongside and also add unique file name to the fiel_set.
   
   at this point, we have files with unique name only and id binded.
   3. update the file_set, filesblob in the indexeddb store.
   4. update userdata at this point
   */

  if (input_files == null) return;
  // fetch file_set with the help of getFileSet() method
  const file_set: Set<string> = new Set<string>(await getFileSet());

  // run a loop for step 2
  const unique_input_files_with_id: CustomFileBlob[] = [];
  Array.from(input_files).map((F) => {
    if (!file_set.has(F.name)) {
      unique_input_files_with_id.push({ _id: uid(FILE_ID_LENGTH), file: F });
      file_set.add(F.name);
    }
  });

  // update the file_set and fileblob store
  await setFileSet(Array.from(file_set));
  await setFileStore([...unique_input_files_with_id, ...files]);
  setFiles([...files, ...unique_input_files_with_id]);

  // update userdata
  const newFileDataArray: FileDataType[] = unique_input_files_with_id.map(
    (F) => {
      return {
        _file_id: F._id,
        background_graphics: false,
        color_mode: "black_&_white",
        file_name: F.file.name,
        headers_footers: false,
        layout: "portrait",
        margins: "default",
        no_of_copies: 1,
        paper_size: "a4",
      };
    },
  );

  const updatedUserData: UserType = {
    ...userData,
    filedataArray: [...userData.filedataArray, ...newFileDataArray],
  };

  setUserData(updatedUserData);
  setDBUserData(updatedUserData);
}

interface fileRemoveFeatureInterface {
  file_name: string;
  userData: UserType;
  setUserData: Dispatch<SetStateAction<UserType>>;
  setFiles: Dispatch<SetStateAction<CustomFileBlob[]>>;
}

export async function fileRemoveFeature({
  file_name,
  userData,
  setFiles,
  setUserData,
}: fileRemoveFeatureInterface) {
  /*
  this database feature function will remove the file from the buffer and filedb store.

  steps: 
  1. check if file_name is empty or not if empty then return early.
  2. run a loop to filter the file_set.
  3. run a loop to filter the file_store.
  4. run a loop to filter the userdata's filedataarray.
  5. update the store with the filtered values and also update the react states.
   */

  if (!file_name) return;

  // step 2
  const file_set: Set<string> = new Set<string>(await getFileSet());
  const isFileRemovedFromSet: boolean = file_set.delete(file_name);

  if (!isFileRemovedFromSet) return;

  // step 3
  const file_store: CustomFileBlob[] = await getFileStore();
  const newFileStore: CustomFileBlob[] = file_store.filter(
    (F) => F.file.name != file_name,
  );

  // step 4
  const filteredFileDataArray: FileDataType[] = userData.filedataArray.filter(
    (FD) => FD.file_name != file_name,
  );
  const updatedUserData: UserType = {
    ...userData,
    filedataArray: filteredFileDataArray,
  };

  // step 5
  setUserData(updatedUserData);
  setFiles(newFileStore);

  setFileStore(newFileStore);
  setDBUserData(updatedUserData);
  setFileSet(Array.from(file_set));
}

interface FileDataUpdateHandlerInterface {
  file_id: string;
  file_data: FileDataType;
  userData: UserType;
  setUserData: Dispatch<SetStateAction<UserType>>;
}

export async function FileDataUpdateHandler({
  file_data,
  userData,
  file_id,
  setUserData,
}: FileDataUpdateHandlerInterface) {
  const newFileDataArray: FileDataType[] = [];
  userData.filedataArray.forEach((FD) => {
    if (FD._file_id == file_id) {
      newFileDataArray.push(file_data);
    } else {
      newFileDataArray.push(FD);
    }
  });
  setUserData({ ...userData, filedataArray: newFileDataArray });
  setDBUserData({ ...userData, filedataArray: newFileDataArray });
}
