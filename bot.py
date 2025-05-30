import asyncio

import nest_asyncio
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from commands import (
    start,
    schedule_command,
    agenda_command,
    homework_command,
    mark_command,
    settings_command,
    absence_command,
)
from utils import synchronization

global bot_


class RighiBot:
    def __init__(self, token):
        self.application = Application.builder().token(token=token).build()
        self.bot = Bot(token=token)

    async def setup(self):
        global bot_
        bot_ = self.bot
        self.application.add_handler(
            CommandHandler(
                command=["start", "cominciare"], callback=start.start_command
            )
        )
        self.application.add_handler(
            CommandHandler(
                command=["schedule", "orario"],
                callback=schedule_command.schedule_command,
            )
        )
        self.application.add_handler(
            CommandHandler(
                command="agenda",
                callback=agenda_command.agenda_command,
            )
        )

        self.application.add_handler(
            CommandHandler(
                command=["tasks", "homework", "compiti"],
                callback=homework_command.homework_command,
            )
        )

        self.application.add_handler(
            CommandHandler(
                command=["marks", "mark", "voti"],
                callback=mark_command.mark_command,
            )
        )

        self.application.add_handler(
            CommandHandler(
                command=["settings", "impostazioni"],
                callback=settings_command.settings_command,
            )
        )

        self.application.add_handler(
            CommandHandler(
                command=["menu"],
                callback=settings_command.menu_command,
            )
        )

        self.application.add_handler(
            CommandHandler(
                command=["language", "lingua"],
                callback=settings_command.language_command,
            )
        )
        self.application.add_handler(
            CommandHandler(
                command=["absence", "assenze"], callback=absence_command.absence_command
            )
        )

        self.application.add_handler(
            MessageHandler(
                callback=start.message_handler, filters=filters.ALL, block=False
            )
        )

        self.application.add_handler(
            CallbackQueryHandler(callback=start.buttons_callback)
        )
        tasks = []
        nest_asyncio.apply()
        tasks.append(asyncio.create_task(synchronization.main_sync()))
        tasks.append(
            asyncio.create_task(
                self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            )
        )
        await asyncio.gather(*tasks)
