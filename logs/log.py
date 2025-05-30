import logging
import random
import string
from pathlib import Path

from config import logs_configuration

logger = logging.getLogger(__name__)


def generate_random_filename() -> str:
    random_filename = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(10)
    )
    return f"logs/{random_filename}.log"


async def log_with_random_path(message: str) -> str or None:
    bot_log = logs_configuration.get_bot_log()

    if bot_log is not None:
        bot_log = Path(generate_random_filename())

        file_handler = logging.handlers.RotatingFileHandler(
            bot_log,
            maxBytes=5 * (2**20),
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s")
        )
        logging.getLogger().addHandler(file_handler)

    logger.error(message)

    if bot_log is not None:
        logging.getLogger().removeHandler(file_handler)

    return bot_log.name.replace(".log", "") if bot_log is not None else None
