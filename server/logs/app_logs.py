import logging
from server.utils.constants import LOG_FILE_PATH

logger = logging.getLogger(__name__)


def configureAppLogger():
    with open(LOG_FILE_PATH, "w") as f:
        f.write("")
    logging.basicConfig(
        filename=LOG_FILE_PATH,
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.DEBUG,
    )
    logger.info("APP Log configured and connected!")
