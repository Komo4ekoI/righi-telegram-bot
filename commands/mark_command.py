import datetime
import json

import telegram.constants
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import formaters
from utils import database
from utils import methods


def get_date(mark: dict):
    return datetime.datetime.strptime(mark["date"], "%d.%m.%Y")


async def mark_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    marks_list = json.loads(user.marks)
    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    if not marks_list:
        return await update.effective_user.send_message(
            text=f"⚠️{translation.translation['NO_REQUEST_DATA']}"
        )

    message_marks_list = marks_list[0:3]

    message = await translation.marks_message(marks_list=message_marks_list)

    keyboard = await get_keyboard(
        translation=translation,
        index=0,
        marks_list_len=len(marks_list),
        message_marks_count=len(message_marks_list),
    )

    if keyboard is not None:
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return await update.effective_user.send_message(
            text=message,
            parse_mode=telegram.constants.ParseMode.HTML,
            reply_markup=markup,
        )

    await update.effective_user.send_message(
        text=message, parse_mode=telegram.constants.ParseMode.HTML
    )


async def get_keyboard(
    translation: formaters.LanguageFormations,
    index: int,
    marks_list_len: int,
    message_marks_count: int,
):
    before_button = InlineKeyboardButton(
        text=f"⬅️{translation.translation['BEFORE_BUTTON']}",
        callback_data="before_marks",
    )
    next_button = InlineKeyboardButton(
        text=f"{translation.translation['NEXT_BUTTON']}➡️",
        callback_data="next_marks",
    )
    keyboard = None

    next_, before_ = False, False

    if index + message_marks_count < marks_list_len:
        next_ = True

    if index > 0:
        before_ = True

    if next_ and before_:
        keyboard = [[before_button, next_button]]
    elif next_ and not before_:
        keyboard = [[next_button]]
    elif not next_ and before_:
        keyboard = [[before_button]]

    return keyboard


async def marks_buttons_callback(update: Update, _: CallbackContext, revers: bool):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        await update.effective_message.delete()
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    marks_list = json.loads(user.marks)
    user_setting = json.loads(user.user_settings)
    translation = formaters.LanguageFormations(language=user_setting["language"])
    await translation.setup()

    if not marks_list:
        return await update.effective_user.send_message(
            text=f"⚠️{translation.translation['NO_REQUEST_DATA']}"
        )

    text_message = update.effective_message.text

    lines = text_message.split("\n")

    date = None
    try:
        split_date = lines[0].split(" ")
        date = f"{split_date[-2]}.{formaters.months[split_date[-1].lower()]}"
    except:
        pass

    if date:
        message_marks_count = None
        if "3️⃣" in text_message:
            message_marks_count = 3
        elif "2️⃣" in text_message:
            message_marks_count = 2
        elif "1️⃣" in text_message:
            message_marks_count = 1

        if not message_marks_count:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        current_date = None

        for mark in marks_list:
            if date in mark["date"]:
                current_date = mark["date"]
                break

        if current_date is not None:
            mark_for_index = methods.find_dict_by_key_value(
                input_list=marks_list, key="date", value=current_date
            )
        else:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        if len(mark_for_index) < 2:
            index = marks_list.index(mark_for_index[0])
        else:
            index = marks_list.index(
                mark_for_index[-1]
            )

        old_index = index

        if not revers:
            index += message_marks_count
            message_marks_list = marks_list[index: index + 3]
        else:
            index = index - 3

            if index < 0:
                index = max(index - 1, index - 2)

            message_marks_list = marks_list[index:old_index]

        if not message_marks_list:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        message = await translation.marks_message(marks_list=message_marks_list)

        keyboard = await get_keyboard(
            translation=translation,
            index=index,
            marks_list_len=len(marks_list),
            message_marks_count=len(message_marks_list),
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
    else:
        await update.effective_message.delete()
        await update.effective_user.send_message(
            text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
        )
