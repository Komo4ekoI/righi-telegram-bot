import asyncio
import logging
import os

from dotenv import load_dotenv, find_dotenv

import bot
from config import logs_configuration
from config import settings

logger = logging.getLogger(__name__)
logs_configuration.setup()

load_dotenv(find_dotenv())

my_pass = str(os.getenv("MY_PASS"))
my_name = str(os.getenv("MY_NAME"))


async def main():
    bot_ = bot.RighiBot(token=settings.BOT_TOKEN)
    await bot_.setup()


asyncio.run(main())
