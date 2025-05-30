import json
import logging

import telegram.constants
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CallbackContext

import formaters
from utils import database
from utils import methods

logger = logging.getLogger(__name__)


async def delete_account_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    keyboard = [
        [
            InlineKeyboardButton(
                text=translation.translation["CONFIRM_BUTTON"],
                callback_data="confirm_account_delete",
            )
        ],
        [
            InlineKeyboardButton(
                text=translation.translation["REJECT_BUTTON"],
                callback_data="reject_account_delete",
            )
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await update.effective_user.send_message(
        text=translation.translation["ACCOUNT_DELETE_CONFIRM_MESSAGE"],
        reply_markup=markup,
        parse_mode=telegram.constants.ParseMode.HTML,
    )


async def confirm_account_delete_callback(update: Update, _: CallbackContext):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    await update.effective_message.delete()
    await database.delete_user(telegram_id=update.effective_user.id)

    await update.effective_user.send_message(
        text=translation.translation["FAREWELL_MESSAGE_ACCOUNT_DELETE"],
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=telegram.constants.ParseMode.HTML,
    )


async def reject_account_delete_callback(update: Update, _: CallbackContext):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    await update.effective_message.delete()

    await update.effective_user.send_message(
        text=translation.translation["DELETE_ACCOUNT_REJECT_MESSAGE"],
        parse_mode=telegram.constants.ParseMode.HTML,
    )
