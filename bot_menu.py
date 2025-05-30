from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import CallbackContext

import formaters
from commands import (
    schedule_command,
    agenda_command,
    homework_command,
    mark_command,
    settings_command,
    delete_account,
)


async def main_menu(language: str) -> ReplyKeyboardMarkup:
    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    keyword = [
        [
            KeyboardButton(text=f"{translation.translation['HOMEWORK_BUTTON']}"),
            KeyboardButton(text=f"{translation.translation['MARKS_BUTTON']}"),
        ],
        [
            KeyboardButton(text=f"{translation.translation['AGENDA_BUTTON']}"),
            KeyboardButton(text=f"{translation.translation['SCHEDULE_BUTTON']}"),
        ],
        [
            KeyboardButton(text=f"{translation.translation['ABSENCE_BUTTON']}"),
            KeyboardButton(text=f"{translation.translation['SETTINGS_BUTTON']}"),
        ],
    ]

    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keyword)
    return markup


async def settings_menu(language: str) -> ReplyKeyboardMarkup:
    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    keyword = [
        [
            KeyboardButton(text=f"{translation.translation['LANGUAGE_BUTTON']}"),
            KeyboardButton(text=f"{translation.translation['DELETE_ACCOUNT_BUTTON']}"),
        ],
        [
            KeyboardButton(text=f"{translation.translation['BACK_TO_MENU_BUTTON']}"),
        ],
    ]

    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keyword)
    return markup


async def schedule_button_callback(update: Update, _: CallbackContext):
    await schedule_command.schedule_command(update=update, _=_)


async def agenda_button_callback(update: Update, _: CallbackContext):
    await agenda_command.agenda_command(update=update, _=_)


async def homework_button_callback(update: Update, _: CallbackContext):
    await homework_command.homework_command(update=update, _=_)


async def marks_button_callback(update: Update, _: CallbackContext):
    await mark_command.mark_command(update=update, _=_)


async def settings_button_callback(update: Update, _: CallbackContext):
    await settings_command.settings_command(update=update, _=_)


async def language_button_callback(update: Update, _: CallbackContext):
    await settings_command.language_command(update=update, _=_)


async def menu_button_callback(update: Update, _: CallbackContext):
    await settings_command.menu_command(update=update, _=_)


async def delete_account_callback(update: Update, _: CallbackContext):
    await delete_account.delete_account_command(update=update, _=_)
