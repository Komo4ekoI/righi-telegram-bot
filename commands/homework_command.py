import datetime
import json
import logging

import telegram.constants
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackContext

import formaters
from config import settings
from utils import database
from utils import methods

logger = logging.getLogger(__name__)


async def homework_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    task_list = json.loads(user.tasks)

    language = json.loads(user.user_settings)["language"]

    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    if not task_list:
        return await update.effective_user.send_message(
            text=f"⚠️{translation.translation['NO_REQUEST_DATA']}"
        )

    current_date = datetime.datetime.now(tz=settings.timezone)

    current_day_tasks = []
    date = None
    dates = []

    for task in task_list:
        day, month, year = map(int, task["date"].split("."))
        date = current_date.replace(day=day, month=month, year=year)
        dates.append(date)

    future_dates = [date for date in dates if date >= current_date]

    if future_dates:
        closest_date = min(future_dates)
    else:
        closest_date = min(dates, key=lambda date: abs(date - current_date))

    closest_date_str = closest_date.strftime("%d.%m.%Y")

    if closest_date_str:
        dicts_for_index = methods.find_dict_by_key_value(
            input_list=task_list, key="date", value=closest_date_str
        )

        index = task_list.index(dicts_for_index[0])
    else:
        try:
            closest_date_str = task_list[0]["date"]
            dicts_for_index = methods.find_dict_by_key_value(
                input_list=task_list, key="date", value=date
            )
            index = 0
            if not dicts_for_index:
                raise IndexError
        except IndexError:
            return await update.effective_user.send_message(
                text=translation.translation["NOT_TASKS_FOUND"]
            )

    finished = False

    while not finished:
        if closest_date_str == task_list[index]["date"]:
            current_day_tasks.append(task_list[index])
            index -= 1
        else:
            finished = True

    message = await translation.day_tasks(tasks=current_day_tasks)
    markup = await get_markup(index=index, task_list=task_list, translation=translation)

    if markup is not None:
        await update.effective_user.send_message(
            text=message,
            parse_mode=telegram.constants.ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
    else:
        await update.effective_user.send_message(
            text=message, parse_mode=telegram.constants.ParseMode.HTML
        )


async def get_markup(index: int, task_list: list, translation):
    before_button = InlineKeyboardButton(
        text=f"⬅️{translation.translation['BEFORE_BUTTON']}",
        callback_data="before_homework",
    )
    next_button = InlineKeyboardButton(
        text=f"{translation.translation['NEXT_BUTTON']}➡️",
        callback_data="next_homework",
    )
    keyboard = None
    task_list_len = len(task_list)

    next_ = False
    before_ = False

    if index < task_list_len:
        before_ = True

    if index >= 0:
        next_ = True

    if next_ and before_:
        keyboard = [[before_button, next_button]]
    elif next_ and not before_:
        keyboard = [[next_button]]
    elif not next_ and before_:
        keyboard = [[before_button]]

    markup = None

    if keyboard is not None:
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    return markup


async def homework_buttons_callback(update: Update, _: CallbackContext, revers: bool):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        await update.effective_message.delete()
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    text_message = update.effective_message.text

    lines = text_message.split("\n")

    date = None
    try:
        split_date = lines[0].split(" ", 1)
        month = formaters.months[split_date[1].lower()]
        year = (
            settings.current_school_start_year
            if int(month) > 8
            else settings.current_school_start_year + 1
        )
        date = f"{int(split_date[0]):02}.{month}.{year}"
    except:
        pass

    user_setting = json.loads(user.user_settings)
    translation = formaters.LanguageFormations(language=user_setting["language"])
    await translation.setup()

    if date:
        user_tasks = json.loads(user.tasks)
        index = 0
        current_day = None

        for task in user_tasks:
            if date == task["date"]:
                current_day = task
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
                index += -1 if not revers else 1
                if date not in user_tasks[index]["date"]:
                    next_day_data = user_tasks[index]
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

        date = next_day_data["date"]

        finished = False
        current_day_tasks = []

        while not finished:
            try:
                if date == user_tasks[index]["date"]:
                    current_day_tasks.append(user_tasks[index])
                    index += -1 if not revers else 1
                else:
                    finished = True
            except IndexError:
                finished = True

        if not current_day_tasks:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        message_list = (
            list(reversed(current_day_tasks)) if not revers else current_day_tasks
        )
        message = await translation.day_tasks(tasks=message_list)

        markup = await get_markup(
            index=index, task_list=user_tasks, translation=translation
        )

        if markup is not None:
            await update.effective_message.edit_text(
                text=message,
                parse_mode=telegram.constants.ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=True,
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
