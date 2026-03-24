import logging

logger = logging.getLogger(__name__)


def configureAppLogger():
    logging.basicConfig(
        filename="./server/logs/app_logs.log",
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.DEBUG,
    )
    logger.info("APP Log configured and connected!")
