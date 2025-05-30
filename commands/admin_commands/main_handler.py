from telegram import Update
from telegram.ext import ContextTypes

from commands.admin_commands import stats
from config import settings


async def command_identification(update: Update, _: ContextTypes.DEFAULT_TYPE):
    message_text = update.effective_message.text

    if not message_text:
        return

    if f"{settings.bot_command_prefix}bot" not in message_text:
        return

    split_message = message_text.split(".")
    command = split_message[1]

    if command == "stats":
        await stats.stats_command(update=update)
