from pathlib import Path
import os

# base directory constants
ROOT_DIR = Path(__file__).parent.parent.parent
SERVER_DIR = os.path.join(ROOT_DIR, "server")
CLIENT_DIR = os.path.join(ROOT_DIR, "client")

# user_records.json file path constant
USER_RECORD_FILE_PATH = os.path.join(CLIENT_DIR, "data", "user_records.json")
DATA_FOLDER_PATH = os.path.join(CLIENT_DIR, "data")

# ip.json file path constant
IP_FILE_PATH = os.path.join(CLIENT_DIR, "ip.json")
PORT = 3000


def get_user_record_filepath() -> str:
    if Path(USER_RECORD_FILE_PATH).is_file():
        return USER_RECORD_FILE_PATH
    else:
        return ""


if __name__ == "__main__":
    print(get_user_record_filepath())
