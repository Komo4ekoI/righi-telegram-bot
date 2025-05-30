import logging
import logging.handlers
import sys
import time
from pathlib import Path

import coloredlogs

from config import settings


def setup(debug_mode=settings.debug_mode) -> None:
    global debug_log, bot_log
    bot_log = None

    format_string = "[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s"
    log_format = logging.Formatter(format_string)
    root_logger = logging.getLogger()

    try:
        if debug_mode:
            root_logger.setLevel(logging.DEBUG)
            debug_log = Path("logs/debug.log")
        else:
            root_logger.setLevel(logging.INFO)
            bot_log = Path("logs/RighiBot.log")
    except PermissionError:
        time.sleep(1)

    log_file = debug_log if debug_mode else bot_log
    log_file.parent.mkdir(exist_ok=True)

    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * (2**20),
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    coloredlogs.DEFAULT_LEVEL_STYLES = {
        **coloredlogs.DEFAULT_LEVEL_STYLES,
        "trace": {"color": 246},
        "critical": {"background": "red"},
        "debug": coloredlogs.DEFAULT_LEVEL_STYLES["info"],
    }

    coloredlogs.DEFAULT_LOG_FORMAT = format_string

    coloredlogs.install(level=logging.INFO, stream=sys.stdout)


def get_bot_log():
    global bot_log
    return bot_log
