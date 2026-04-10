import os
from pathlib import Path

# base directory constants
ROOT_DIR: Path = Path(__file__).parent.parent.parent
SERVER_DIR: Path = ROOT_DIR / "server"
ASSETS_PATH: str = str(SERVER_DIR / "assets")
CLIENT_DIR: Path = ROOT_DIR / "client"

# user_records.json file path constant
USER_RECORD_FILE_PATH: str = str(CLIENT_DIR / "data" / "user_records.json")
DATA_FOLDER_PATH: str = str(CLIENT_DIR / "data")

PORT: int = 3000

# shop identity & peer discovery
SHOP_CONFIG_PATH: str = str(CLIENT_DIR / "shop_config.json")
DISCOVERED_PEERS_PATH: str = str(CLIENT_DIR / "data" / "discovered_peers.json")

# logging file path constant
LOG_FILE_PATH: str = str(SERVER_DIR / "logs" / "app_logs.log")

# queue and storage paths
PRINT_QUEUE_FILE_PATH: str = str(CLIENT_DIR / "data" / "print_queue.json")
COST_FILE_PATH: str = str(CLIENT_DIR / "public" / "cost.json")
FILE_STORAGE_PATH: str = str(CLIENT_DIR / "data" / "print_job_file_storage")

# Python API server
PYTHON_API_PORT: int = 8000

# SQLite database
DB_PATH: str = str(CLIENT_DIR / "data" / "qprint.db")

# Analytics cloud API (override via ANALYTICS_CLOUD_URL env var if self-hosting)
ANALYTICS_CLOUD_URL: str = os.getenv("ANALYTICS_CLOUD_URL", "https://qprint-analytics.vercel.app")


def get_user_record_filepath() -> str:
    if Path(USER_RECORD_FILE_PATH).is_file():
        return USER_RECORD_FILE_PATH
    raise FileNotFoundError(f"user_records.json not found at: {USER_RECORD_FILE_PATH}")


if __name__ == "__main__":
    print(get_user_record_filepath())
