import datetime
import json
import logging

import telegram.constants
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import formaters
from config import settings
from utils import database
from utils import methods

logger = logging.getLogger(__name__)


async def schedule_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    _schedule = json.loads(user.schedule)
    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    if not _schedule:
        return await update.effective_user.send_message(
            text=f"⚠️{translation.translation['NO_REQUEST_DATA']}"
        )

    message, markup = await get_full_message(_schedule=_schedule, language=language)

    if markup is not None:
        return await update.effective_user.send_message(
            text=message,
            parse_mode=telegram.constants.ParseMode.HTML,
            reply_markup=markup,
        )

    await update.effective_user.send_message(
        text=message, parse_mode=telegram.constants.ParseMode.HTML
    )


async def get_full_message(_schedule: list, language: str):
    current_date = datetime.datetime.now(tz=settings.timezone)
    dates = []

    for schedule in _schedule:
        year, month, day = map(int, schedule["data_fine_tradotta_iso"].split("-"))
        date = current_date.replace(year=year, month=month, day=day)
        dates.append(date)

    future_dates = [date for date in dates if date >= current_date]

    if future_dates:
        closest_date = min(future_dates)
    else:
        closest_date = dates[-1]

    day = str(closest_date.date())

    lessons_with_date = methods.find_dict_by_key_value(
        input_list=_schedule, key="data_fine_tradotta_iso", value=day
    )
    lesson = lessons_with_date[0]

    current_day_lessons = []

    if closest_date:
        index = _schedule.index(lesson)
        finished = False

        while not finished:
            if str(day) == _schedule[index]["data_fine_tradotta_iso"] and index < len(_schedule) - 1:
                current_day_lessons.append(_schedule[index])
                index += 1
            else:
                finished = True

        translation = formaters.LanguageFormations(language=language)
        await translation.setup()
        message = await translation.day_schedule(lessons=current_day_lessons)

        next_ = False
        before_ = False
        schedule_len = len(_schedule)

        if index < schedule_len - 1:
            next_ = True

        if index > 0:
            before_ = True

        before_button = InlineKeyboardButton(
            text=f"⬅️{translation.translation['BEFORE_BUTTON']}",
            callback_data="before_schedule",
        )
        next_button = InlineKeyboardButton(
            text=f"{translation.translation['NEXT_BUTTON']}➡️",
            callback_data="next_schedule",
        )
        keyboard, markup = None, None

        if before_ and next_:
            keyboard = [[before_button, next_button]]
        elif not before_ and next_:
            keyboard = [[next_button]]
        elif before_ and not next_:
            keyboard = [[before_button]]

        if keyboard is not None:
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        return message, markup


async def schedule_buttons_callback(update: Update, _: CallbackContext, revers: bool):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        await update.effective_message.delete()
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    text_message = update.effective_message.text

    lines = text_message.split("\n")
    date = None
    try:
        data = lines[0].split(": ", 1)[1]

        split_data = data.split(" ")
        date = f"{formaters.months[split_data[1].lower()]}-{split_data[0]}"
    except:
        pass

    user_setting = json.loads(user.user_settings)
    translation = formaters.LanguageFormations(language=user_setting["language"])
    await translation.setup()

    if date:
        user_schedule = json.loads(user.schedule)
        index = 0
        current_day = None

        for schedule in user_schedule:
            if date in schedule["data_inizio_tradotta_iso"]:
                current_day = schedule
                break
            index += 1
        if not current_day:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        next_day_data = None

        try:
            new_date_found = False
            while not new_date_found:
                index += 1 if not revers else -1
                if date not in user_schedule[index]["data_inizio_tradotta_iso"]:
                    next_day_data = user_schedule[index]
                    new_date_found = True
        except:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        if not next_day_data:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        date = next_day_data["data_inizio_tradotta_iso"]

        finished = False
        current_day_lessons = []

        while not finished:
            if date == user_schedule[index]["data_fine_tradotta_iso"] and index < len(user_schedule) - 1:
                current_day_lessons.append(user_schedule[index])
                index += 1 if not revers else -1
            else:
                finished = True

        if not current_day_lessons:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        message_list = (
            current_day_lessons if not revers else list(reversed(current_day_lessons))
        )
        message = await translation.day_schedule(lessons=message_list)

        next_ = False
        before_ = False
        index += 1 if revers else 0
        schedule_len = len(user_schedule)

        if index < schedule_len - 1:
            next_ = True

        if index > 0:
            before_ = True

        before_button = InlineKeyboardButton(
            text=f"⬅️{translation.translation['BEFORE_BUTTON']}",
            callback_data="before_schedule",
        )
        next_button = InlineKeyboardButton(
            text=f"{translation.translation['NEXT_BUTTON']}➡️",
            callback_data="next_schedule",
        )

        if next_ and before_:
            keyboard = [[before_button, next_button]]
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await update.effective_message.edit_text(
                text=message,
                parse_mode=telegram.constants.ParseMode.HTML,
                reply_markup=markup,
            )
        elif next_ and not before_:
            keyboard = [[next_button]]
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await update.effective_message.edit_text(
                text=message,
                parse_mode=telegram.constants.ParseMode.HTML,
                reply_markup=markup,
            )
        elif not next_ and before_:
            keyboard = [[before_button]]
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
