import json
import logging

import telegram.constants
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import bot_menu
import formaters
from utils import database
from utils import methods

logger = logging.getLogger(__name__)


async def language_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    keyboard = [
        [InlineKeyboardButton(text="🇮🇹Italiano", callback_data="it")],
        [InlineKeyboardButton(text="🇬🇧English", callback_data="en")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await update.effective_user.send_message(
        text=translation.translation["LANGUAGE_MESSAGE"],
        reply_markup=markup,
        parse_mode=telegram.constants.ParseMode.HTML,
    )


async def settings_command(update: Update, _: CallbackContext):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    await update.effective_user.send_message(
        text=translation.translation["SETTINGS_MESSAGE"],
        reply_markup=await bot_menu.settings_menu(language=language),
    )


async def menu_command(update: Update, _: CallbackContext):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    await update.effective_user.send_message(
        text=translation.translation["TO_MENU_MESSAGE"],
        reply_markup=await bot_menu.main_menu(language=language),
    )
