from threading import Thread
from subprocess import Popen
from ip_config import set_ip_config
from server.logs.app_logs import configureAppLogger
import logging
from port_killer import free_port
from server.utils.constants import PORT

logger = logging.getLogger(__name__)


def start_web_app():
    Popen(["npm", "run", "dev"], cwd="client")


if __name__ == "__main__":
    # logging configuration
    configureAppLogger()

    # run the free_port.py script to free the port 3000 if used
    free_port(PORT)

    # ip configuration and settlement on the .env file
    set_ip_config()

    web_executor = Thread(target=start_web_app, daemon=True)
    web_executor.start()
    web_executor.join()
