import logging
from os import getenv

import pytz
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

test_mode = bool(getenv("TEST_MODE", False))

BOT_TOKEN = getenv("BOT_TOKEN")
if test_mode:
    BOT_TOKEN = getenv("TEST_BOT_TOKEN")

if BOT_TOKEN is None:
    logger.critical("BOT_TOKEN is missing!")

debug_mode = bool(getenv("DEBUG_MODE", False))

DATABASE_FILE_NAME = "QuadernoDB"
if test_mode:
    DATABASE_FILE_NAME = "QuadernoDB_TESTS"

try:
    timezone = pytz.timezone("Europe/Rome")
except pytz.UnknownTimeZoneError:
    logger.critical("Unknown TimeZone!")

current_school_start_year = 2024

owner_ids = [697632256]

bot_command_prefix = "!"
