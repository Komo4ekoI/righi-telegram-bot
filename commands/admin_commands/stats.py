from telegram import Update
from telegram.constants import ParseMode

from utils import database


async def stats_command(update: Update):
    users = await database.get_all_users()
    users_wait = await database.get_all_users_wait()

    users_count = len(users)
    users_wait_count = len(users_wait)

    message = (
        "<b>BOT STAT</b>\n"
        f"<b>Users count</b>: {users_count}\n"
        f"<b>Users in register count</b>: {users_wait_count}"
    )

    await update.effective_user.send_message(text=message, parse_mode=ParseMode.HTML)
