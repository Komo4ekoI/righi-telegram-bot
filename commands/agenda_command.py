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


async def agenda_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user = await database.find_user_by_telegram_id(telegram_id=update.effective_user.id)

    if not user:
        return await methods.delete_user_data(telegram_id=update.effective_user.id)

    agenda_list = json.loads(user.agenda)

    language = json.loads(user.user_settings)["language"]
    translation = formaters.LanguageFormations(language=language)
    await translation.setup()

    if not agenda_list:
        return await update.effective_user.send_message(
            text=f"⚠️{translation.translation['NO_REQUEST_DATA']}"
        )

    agenda_list = list(reversed(agenda_list))

    current_date = datetime.datetime.now(tz=settings.timezone)
    dates = []

    for agenda in agenda_list:
        day, month, year = map(int, agenda["date"].split("."))
        date = current_date.replace(day=day, month=month, year=year)
        dates.append(date)

    future_dates = [date for date in dates if date >= current_date]

    if future_dates:
        closest_date = min(future_dates)
    else:
        closest_date = min(dates, key=lambda date: abs(date - current_date))

    closest_date_str = closest_date.strftime("%d.%m.%Y")

    day_agenda_list = methods.find_dict_by_key_value(
        input_list=agenda_list, key="date", value=closest_date_str
    )

    message = await translation.agenda_message(agenda_list=day_agenda_list)

    index = agenda_list.index(day_agenda_list[-1])

    items_count = len(day_agenda_list)

    agenda_list_len = len(agenda_list)

    keyboard = await get_keyboard(
        translation=translation,
        index=index,
        agenda_list_len=agenda_list_len,
        items_count=items_count - 1,
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


async def get_keyboard(
    translation: formaters.LanguageFormations,
    index: int,
    agenda_list_len: int,
    items_count: int,
):
    before_button = InlineKeyboardButton(
        text=f"⬅️{translation.translation['BEFORE_BUTTON']}",
        callback_data="before_agenda",
    )
    next_button = InlineKeyboardButton(
        text=f"{translation.translation['NEXT_BUTTON']}➡️",
        callback_data="next_agenda",
    )
    keyboard = None

    next_, before_ = False, False

    if index + 1 < agenda_list_len:
        before_ = True

    if index - items_count > 0:
        next_ = True

    if next_ and before_:
        keyboard = [[before_button, next_button]]
    elif next_ and not before_:
        keyboard = [[next_button]]
    elif not next_ and before_:
        keyboard = [[before_button]]

    return keyboard


async def agenda_buttons_callback(update: Update, _: CallbackContext, revers: bool):
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
        agenda = json.loads(user.agenda)
        agenda = list(reversed(agenda))
        agenda_for_index = methods.find_dict_by_key_value(
            input_list=agenda, key="date", value=date
        )

        if not agenda_for_index:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        index = agenda.index(agenda_for_index[-1])

        finished = False
        new_date = None

        while not finished:
            index += -1 if not revers else 1
            if agenda[index]["date"] != date:
                new_date = agenda[index]["date"]
                finished = True

        if not new_date:
            await update.effective_message.delete()
            return await update.effective_user.send_message(
                text=f"\u26A0{translation.translation['NOT_DATA_FOUND']}"
            )

        day_agenda_list = methods.find_dict_by_key_value(
            input_list=agenda, key="date", value=new_date
        )

        items_count = len(day_agenda_list)

        message = await translation.agenda_message(agenda_list=day_agenda_list)

        agenda_list_len = len(agenda)

        keyboard = await get_keyboard(
            translation=translation,
            index=index,
            agenda_list_len=agenda_list_len,
            items_count=items_count - 1,
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
