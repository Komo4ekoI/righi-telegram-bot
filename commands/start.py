import asyncio
import json

import telegram.constants
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import bot_menu
import formaters
from commands import (
    schedule_command,
    agenda_command,
    homework_command,
    mark_command,
    delete_account,
    absence_command,
)
from commands.admin_commands import main_handler
from config import settings
from mastercom_api import (
    agenda,
    marks,
    auth_functions,
    tasks,
    schedule,
    messenger,
    absence,
)
from utils import database, methods


async def warning_message(update: Update, translation):
    buttons = [
        [InlineKeyboardButton(text="\u2705Confermare", callback_data="confirm")],
        [InlineKeyboardButton(text="\u274CRifiutare", callback_data="reject")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await update.message.reply_text(
        text=f"\u26A0\u26A0\u26A0\n{translation.translation['MUST_CONFIRM_MESSAGE']}",
        parse_mode=telegram.constants.ParseMode.HTML,
        reply_markup=markup,
    )


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    database_result = await database.find_user_by_telegram_id(
        telegram_id=update.effective_user.id
    )

    if database_result:
        user_settings = json.loads(database_result.user_settings)
        translation = formaters.LanguageFormations(language=user_settings["language"])
        await translation.setup()
        return await update.effective_user.send_message(
            text=f"{translation.translation['ALREADY_REGISTERED_MESSAGE']}\U0001F60E",
            reply_markup=await bot_menu.main_menu(language=user_settings["language"]),
        )

    translation = formaters.LanguageFormations(language="it")
    await translation.setup()

    if user := await database.user_in_wait(telegram_id=update.effective_user.id):
        if not user.confirmed:
            await warning_message(update=update, translation=translation)
        else:
            if not user.login:
                await update.message.reply_text(
                    text=translation.translation["NEED_LOGIN_REQUEST"]
                )

            elif not user.password:
                await update.message.reply_text(
                    text=translation.translation["NEED_PASSWORD_REQUEST"]
                )

    else:
        await database.add_user_to_wait(telegram_id=update.effective_user.id)
        await update.message.reply_text(text=translation.translation["WELCOME_MESSAGE"])
        await warning_message(update=update, translation=translation)


async def buttons_callback(update: Update, _: CallbackContext):
    query = update.callback_query

    if not query:
        return

    data = query.data

    if not data:
        return

    if data == "confirm":
        translation = formaters.LanguageFormations(language="it")
        await translation.setup()
        await database.update_wait_user_by_telegram_id(
            telegram_id=update.effective_user.id, confirmed=True
        )
        await update.effective_user.send_message(
            text=translation.translation["LOGIN_REQUEST"]
        )
        await update.effective_message.delete()
    elif data == "reject":
        translation = formaters.LanguageFormations(language="it")
        await translation.setup()
        await update.effective_user.send_message(
            text=f"{translation.translation['FAREWELL_MESSAGE']}\U0001F613"
        )
        await update.effective_message.delete()
    elif data == "it":
        user = await database.find_user_by_telegram_id(
            telegram_id=update.effective_user.id
        )

        if not user:
            await update.effective_message.delete()
            return await methods.delete_user_data(telegram_id=update.effective_user.id)

        translation = formaters.LanguageFormations(language="it")
        await translation.setup()
        await database.set_user_language(
            telegram_id=update.effective_user.id, language="it"
        )
        await update.effective_user.send_message(
            text=f"{translation.translation['SUCCESSFUL_LANGUAGE_CHANGE']}",
            reply_markup=await bot_menu.main_menu(language="it"),
        )
        await update.effective_message.delete()
    elif data == "en":
        user = await database.find_user_by_telegram_id(
            telegram_id=update.effective_user.id
        )

        if not user:
            await update.effective_message.delete()
            return await methods.delete_user_data(telegram_id=update.effective_user.id)

        translation = formaters.LanguageFormations(language="en")
        await translation.setup()
        await database.set_user_language(
            telegram_id=update.effective_user.id, language="en"
        )
        await update.effective_user.send_message(
            text=f"{translation.translation['SUCCESSFUL_LANGUAGE_CHANGE']}",
            reply_markup=await bot_menu.main_menu(language="en"),
        )
        await update.effective_message.delete()
    elif data == "next_schedule":
        await schedule_command.schedule_buttons_callback(
            update=update, _=_, revers=False
        )
    elif data == "before_schedule":
        await schedule_command.schedule_buttons_callback(
            update=update, _=_, revers=True
        )
    elif data == "next_agenda":
        await agenda_command.agenda_buttons_callback(update=update, _=_, revers=False)
    elif data == "before_agenda":
        await agenda_command.agenda_buttons_callback(update=update, _=_, revers=True)
    elif data == "next_homework":
        await homework_command.homework_buttons_callback(
            update=update, _=_, revers=False
        )
    elif data == "before_homework":
        await homework_command.homework_buttons_callback(
            update=update, _=_, revers=True
        )
    elif data == "next_marks":
        await mark_command.marks_buttons_callback(update=update, _=_, revers=False)
    elif data == "before_marks":
        await mark_command.marks_buttons_callback(update=update, _=_, revers=True)
    elif data == "confirm_account_delete":
        await delete_account.confirm_account_delete_callback(update=update, _=_)
    elif data == "reject_account_delete":
        await delete_account.reject_account_delete_callback(update=update, _=_)
    elif data == "next_absence":
        await absence_command.absence_button_callback(update=update, _=_, revers=False)
    elif data == "before_absence":
        await absence_command.absence_button_callback(update=update, _=_, revers=True)


async def message_handler(update: Update, _: CallbackContext):
    text = update.message.text
    if not text:
        return

    if not await login_and_password_handler(update=update, _=_):
        return

    translation_it = formaters.LanguageFormations(language="it")
    translation_en = formaters.LanguageFormations(language="en")
    await translation_it.setup()
    await translation_en.setup()

    if (
        text == translation_en.translation["SCHEDULE_BUTTON"]
        or text == translation_it.translation["SCHEDULE_BUTTON"]
    ):
        await bot_menu.schedule_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["AGENDA_BUTTON"]
        or text == translation_it.translation["AGENDA_BUTTON"]
    ):
        await bot_menu.agenda_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["HOMEWORK_BUTTON"]
        or text == translation_it.translation["HOMEWORK_BUTTON"]
    ):
        await bot_menu.homework_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["MARKS_BUTTON"]
        or text == translation_it.translation["MARKS_BUTTON"]
    ):
        await bot_menu.marks_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["SETTINGS_BUTTON"]
        or text == translation_it.translation["SETTINGS_BUTTON"]
    ):
        await bot_menu.settings_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["LANGUAGE_BUTTON"]
        or text == translation_it.translation["LANGUAGE_BUTTON"]
    ):
        await bot_menu.language_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["BACK_TO_MENU_BUTTON"]
        or text == translation_it.translation["BACK_TO_MENU_BUTTON"]
    ):
        await bot_menu.menu_button_callback(update=update, _=_)
    elif (
        text == translation_en.translation["DELETE_ACCOUNT_BUTTON"]
        or text == translation_it.translation["DELETE_ACCOUNT_BUTTON"]
    ):
        await bot_menu.delete_account_callback(update=update, _=_)
    elif (
        text == translation_en.translation["ABSENCE_BUTTON"]
        or text == translation_it.translation["ABSENCE_BUTTON"]
    ):
        await absence_command.absence_command(update=update, _=_)

    if update.effective_user.id in settings.owner_ids:
        await main_handler.command_identification(update=update, _=_)


async def login_and_password_handler(update: Update, _: CallbackContext):
    if not (user := await database.user_in_wait(telegram_id=update.effective_user.id)):
        return True

    if not user.confirmed:
        return True

    if user.login:
        pass
    else:
        login = update.effective_message.text
        translation = formaters.LanguageFormations(language="it")
        await translation.setup()
        if not login:
            await update.effective_user.send_message(
                text=f"{translation.translation['LOGIN_RETRIEVAL_ERROR']}"
            )
            return False
        try:
            int(login)
            await database.set_user_wait_login(
                telegram_id=update.effective_user.id, login=login
            )
            await update.effective_user.send_message(
                text=f"{translation.translation['PASSWORD_REQUEST']}"
            )
            await update.message.delete()
            return False
        except ValueError:
            await update.effective_user.send_message(
                text=f"{translation.translation['NON_DIGIT_LOGIN']}"
            )
            return False

    if not user.password or user.password:
        password = update.effective_message.text
        translation = formaters.LanguageFormations(language="it")
        await translation.setup()
        if password:
            await database.set_user_wait_password(
                telegram_id=update.effective_user.id, password=password
            )
            message = await update.effective_user.send_message(
                text=f"{translation.translation['AUTH_ATTEMPT']}"
            )
            await update.effective_message.delete()
            if user_data := await user_register(
                login=user.login,
                password=password,
                telegram_id=update.effective_user.id,
            ):
                await message.delete()
                await update.effective_user.send_message(
                    text=await translation.welcome_message(user_data=user_data),
                    reply_markup=await bot_menu.main_menu(language="it"),
                    parse_mode=telegram.constants.ParseMode.HTML,
                )
                await database.delete_user_from_wait(
                    telegram_id=update.effective_user.id
                )

                buttons = [
                    [InlineKeyboardButton(text="🇮🇹Italiano", callback_data="it")],
                    [InlineKeyboardButton(text="🇬🇧English", callback_data="en")],
                ]
                markup = InlineKeyboardMarkup(inline_keyboard=buttons)
                await asyncio.sleep(10)
                await update.effective_user.send_message(
                    text=f"{translation.translation['LANGUAGE_SELECTION_PROPOSE']}",
                    reply_markup=markup,
                )
                return False
            else:
                await message.delete()
                await update.effective_user.send_message(
                    text=f"\u26A0{translation.translation['LOGIN_ERROR_MESSAGE']}"
                )
                await database.set_user_wait_login(
                    telegram_id=update.effective_user.id, login=""
                )
                await database.set_user_wait_password(
                    telegram_id=update.effective_user.id, password=""
                )
                await update.effective_user.send_message(
                    text=f"{translation.translation['NEED_LOGIN_REQUEST']}"
                )
                return False
        else:
            await update.effective_user.send_message(
                text=f"{translation.translation['PASSWORD_RETRIEVAL_ERROR']}"
            )
            return False
    return True


async def user_register(login: str, password: str, telegram_id: int):
    try:
        resp = await auth_functions.fast_auth(user=login, password=password)
    except Exception:
        return False
    if not resp[0]:
        return False
    tasks_ = [
        asyncio.create_task(
            auth_functions.get_user_data(
                messenger_cookie=resp[2], PHPSESSID_cookie=resp[1]
            )
        ),
        asyncio.create_task(marks.get_user_marks(user=login, password=password)),
        asyncio.create_task(tasks.get_user_tasks(user=login, password=password)),
        asyncio.create_task(agenda.get_user_agenda(user=login, password=password)),
        asyncio.create_task(schedule.get_user_schedule(user=login, password=password)),
        asyncio.create_task(
            messenger.get_user_messages(
                messenger_cookie=resp[2], PHPSESSID_cookie=resp[1]
            )
        ),
        asyncio.create_task(absence.get_user_absence(user=login, password=password)),
    ]
    try:
        response = await asyncio.gather(*tasks_)
    except Exception:
        return False
    user_data_resp = response[0]
    marks_resp = response[1]
    tasks_resp = response[2]
    agenda_resp = response[3]
    schedule_resp = response[4]
    messages_resp = response[5]
    absence_resp = response[6]

    if (
        not marks_resp[0]
        or not tasks_resp[0]
        or not agenda_resp[0]
        or not user_data_resp
        or not schedule_resp[0]
        or not messages_resp[0]
        or not absence_resp[0]
    ):
        return False

    await database.add_user(
        telegram_id=telegram_id,
        user_id=user_data_resp["results"]["properties"]["code"],
        login=login,
        password=password,
        agenda=agenda_resp[1],
        marks=marks_resp[1],
        schedule=schedule_resp[1],
        user_data=user_data_resp,
        tasks=tasks_resp[1],
        user_settings={"language": "it"},
        messages=messages_resp[1],
        absence=absence_resp[1],
    )
    return user_data_resp
