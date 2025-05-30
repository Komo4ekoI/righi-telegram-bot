import json
import logging

import telegram.constants
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import formaters
from utils import database
from utils import methods

logger = logging.getLogger(__name__)


async def get_keyboard(
    translation: formaters.LanguageFormations,
    last_index: int,
    list_len: int,
    items_count: int,
):
    before_button = InlineKeyboardButton(
        text=f"⬅️{translation.translation['BEFORE_BUTTON']}",
        callback_data="before_absence",
    )
    next_button = InlineKeyboardButton(
        text=f"{translation.translation['NEXT_BUTTON']}➡️",
        callback_data="next_absence",
    )
    keyboard = None

    next_, before_ = False, False

    if last_index + 1 < list_len:
        next_ = True

    if last_index - items_count > 0:
        before_ = True

    if next_ and before_:
        keyboard = [[before_button, next_button]]
    elif next_ and not before_:
        keyboard = [[next_button]]
    elif not next_ and before_:
        keyboard = [[before_button]]

    return keyboard


async def absence_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    absence_list = json.loads(user.absence)

    language = json.loads(user.user_settings)["language"]
    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    if not absence_list:
        return await update.effective_user.send_message(
            text=f"{translation.translation['NO_ABSENCE_EXIST']}"
        )

    absences_for_sending = absence_list[:3]

    message = (await translation.absence_message(absence_list=absences_for_sending))[
        :-1
    ] + f"{translation.translation['ONLY_UNCONFIRMED_ABSENCE']}"

    keyboard = await get_keyboard(
        translation=translation,
        last_index=absence_list.index(absences_for_sending[-1]),
        list_len=len(absence_list),
        items_count=len(absences_for_sending),
    )

    if keyboard is not None:
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await update.effective_user.send_message(
            text=message,
            parse_mode=telegram.constants.ParseMode.HTML,
            reply_markup=markup,
        )
    else:
        await update.effective_user.send_message(
            text=message, parse_mode=telegram.constants.ParseMode.HTML
        )


async def absence_button_callback(update: Update, _: CallbackContext, revers: bool):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        await update.effective_message.delete()
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    absence_list: list = json.loads(user.absence)
    user_setting = json.loads(user.user_settings)
    translation = formaters.LanguageFormations(language=user_setting["language"])
    await translation.setup()

    if not absence_list:
        return await update.effective_user.send_message(
            text=f"{translation.translation['NO_ABSENCE_EXIST']}"
        )

    text_message = update.effective_message.text

    message_marks_count = 1
    date = None
    try:
        if "3️⃣" in text_message:
            split_date = text_message.split("3️⃣")
            message_marks_count = 3
        elif "2️⃣" in text_message:
            split_date = text_message.split("2️⃣")
            message_marks_count = 2
        else:
            split_date = text_message.split("1️⃣")
            message_marks_count = 1

        data = split_date[-1].split(" ")
        day, mont, year_data = (
            data[1].zfill(2),
            formaters.months[data[2].lower()],
            data[3],
        )
        split_year = year_data.split("\n")
        year = split_year[0]
        date = f"{year}.{mont}.{day}"
    except:
        pass

    if not date:
        await update.effective_message.delete()
        return await update.effective_user.send_message(
            text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
        )

    current_absence = None

    for absence in absence_list:
        if absence["date"] == date:
            current_absence = absence
            break

    if not current_absence:
        await update.effective_message.delete()
        return await update.effective_user.send_message(
            text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
        )

    index = absence_list.index(current_absence)

    if not revers:
        absence_to_send = absence_list[index + 1 : index + 4]
        last_index = absence_list.index(absence_to_send[-1])
    else:
        index -= message_marks_count - 1
        min_index = max(0, index - 3)

        absence_to_send = absence_list[min_index:index]
        last_index = absence_list.index(absence_to_send[-1])

    if not absence_to_send:
        await update.effective_message.delete()
        return await update.effective_user.send_message(
            text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
        )

    message = await translation.absence_message(absence_list=absence_to_send)

    keyboard = await get_keyboard(
        translation=translation,
        last_index=last_index,
        list_len=len(absence_list),
        items_count=len(absence_to_send),
    )

    if keyboard is not None:
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await update.effective_message.edit_text(
            text=message,
            parse_mode=telegram.constants.ParseMode.HTML,
            reply_markup=markup,
        )
    else:
        await update.effective_message.edit_text(
            text=message, parse_mode=telegram.constants.ParseMode.HTML
        )
