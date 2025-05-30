import logging
import traceback

import telegram
import telegram.constants

import bot
import formaters

logger = logging.getLogger(__name__)


async def send_message(telegram_id: int, message: str, markup=None):
    try:
        if markup is None:
            await bot.bot_.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=telegram.constants.ParseMode.HTML,
                pool_timeout=120,
                connect_timeout=10,
            )
        else:
            await bot.bot_.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=telegram.constants.ParseMode.HTML,
                reply_markup=markup,
                pool_timeout=120,
                connect_timeout=10,
            )
    except telegram.error.TelegramError:
        logger.error(
            await formaters.generate_error_message(
                text="On sending message error!",
                telegram_id=telegram_id,
                error_message=traceback.format_exc(),
            )
        )


async def send_file(telegram_id: int, file_path: str):
    try:
        document = open(file_path, "rb")
        await bot.bot_.send_document(
            chat_id=telegram_id,
            document=document,
            pool_timeout=120,
            connect_timeout=10,
        )
    except telegram.error.TelegramError:
        logger.error(
            await formaters.generate_error_message(
                text="On sending message error!",
                telegram_id=telegram_id,
                error_message=traceback.format_exc(),
            )
        )
