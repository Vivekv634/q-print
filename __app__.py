from threading import Thread
from subprocess import Popen


def start_web_app():
    Popen(["npm", "run", "dev"], cwd="client")


def start_server():
    Popen(["uvicorn", "server_api:app", "--reload"], cwd="server")


if __name__ == "__main__":
    web_executor = Thread(target=start_web_app, daemon=True)
    server_executor = Thread(target=start_server, daemon=True)

    web_executor.start()
    server_executor.start()

    web_executor.join()
