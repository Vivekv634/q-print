from threading import Thread
from subprocess import Popen
from ip_config import set_ip_config


def start_web_app():
    Popen(["npm", "run", "dev"], cwd="client")


if __name__ == "__main__":
    # ip configuration and settlement on the .env file
    set_ip_config()
    print("\nCONFIGURATION:    IP address configured and saved in ip.json file\n")

    web_executor = Thread(target=start_web_app, daemon=True)

    web_executor.start()

    web_executor.join()
