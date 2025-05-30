import asyncio
import copy
import datetime
import json
import logging
import traceback

import telegram.error

import bot_menu
import formaters
import utils.telegram_api
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
from utils import database, methods, telegram_api

logger = logging.getLogger(__name__)


def custom_key(item):
    return datetime.datetime.strptime(item["date"], "%d.%m.%Y")


async def possible_message(user_messages: list[dict], message: dict) -> bool:
    possible = True

    message_name = message["name"]

    for old_message in user_messages:
        if old_message["name"] == message_name:
            possible = False
            break

    return possible


async def sync_user(user: database.User) -> None:
    marks_resp = await marks.get_user_marks(user=user.login, password=user.password)
    tasks_resp = await tasks.get_user_tasks(user=user.login, password=user.password)
    agenda_resp = await agenda.get_user_agenda(user=user.login, password=user.password)
    schedule_resp = await schedule.get_user_schedule(
        user=user.login, password=user.password
    )
    absence_resp = await absence.get_user_absence(
        user=user.login, password=user.password
    )

    # tasks_ = [
    #     asyncio.create_task(
    #         marks.get_user_marks(user=user.login, password=user.password)
    #     ),
    #     asyncio.create_task(
    #         tasks.get_user_tasks(user=user.login, password=user.password)
    #     ),
    #     asyncio.create_task(
    #         agenda.get_user_agenda(user=user.login, password=user.password)
    #     ),
    #     asyncio.create_task(
    #         schedule.get_user_schedule(user=user.login, password=user.password)
    #     ),
    # ]

    auth_resp = await auth_functions.fast_auth(user=user.login, password=user.password)
    user_data_resp = None
    messenger_resp = None

    if auth_resp[0]:
        user_data_resp = await auth_functions.get_user_data(
            PHPSESSID_cookie=auth_resp[1], messenger_cookie=auth_resp[2]
        )

        messenger_resp = await messenger.get_user_messages(
            PHPSESSID_cookie=auth_resp[1], messenger_cookie=auth_resp[2]
        )

        # tasks_.append(
        #     asyncio.create_task(
        #         auth_functions.get_user_data(
        #             PHPSESSID_cookie=auth_resp[1], messenger_cookie=auth_resp[2]
        #         )
        #     )
        # )
        # tasks_.append(
        #     asyncio.create_task(
        #         messenger.get_user_messages(
        #             PHPSESSID_cookie=auth_resp[1], messenger_cookie=auth_resp[2]
        #         )
        #     ),
        # )
    else:
        logger.warning(
            f"\nOn synchronization login error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {auth_resp[1]}"
        )

    # response = await asyncio.gather(*tasks_)

    # marks_resp = response[0]
    # tasks_resp = response[1]
    # agenda_resp = response[2]
    # schedule_resp = response[3]

    # user_data_resp = None
    # messenger_resp = None
    # try:
    #     user_data_resp = response[4]
    #     messenger_resp = response[5]
    # except KeyError:
    #     pass

    if (
        not marks_resp[0]
        and not tasks_resp[0]
        and not agenda_resp[0]
        and not user_data_resp
        and not messenger_resp[0]
        and not absence_resp[0]
    ):
        logger.warning(
            f"\nOn user synchronization error!\nTelegram ID: {user.telegram_id}"
        )
        return

    user_settings: dict = json.loads(user.user_settings)
    translation = formaters.LanguageFormations(language=user_settings["language"])
    await translation.setup()

    # Обработка списка оценок
    if marks_resp[0]:
        old_user_marks = json.loads(user.marks)
        new_user_marks = marks_resp[1]

        marks_ = [item for item in new_user_marks if item not in old_user_marks]

        if marks_:
            for mark in marks_:
                await utils.telegram_api.send_message(
                    telegram_id=user.telegram_id,
                    message=await translation.new_mark_message(mark=mark),
                )

            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, marks=new_user_marks
            )
    else:
        logger.warning(
            f"\nOn user marks synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {marks_resp[1]}"
        )

    # Обработка списка домашнего задания
    if tasks_resp[0]:
        old_user_tasks = json.loads(user.tasks)
        new_user_tasks = tasks_resp[1]

        user_tasks = [item for item in new_user_tasks if item not in old_user_tasks]

        if user_tasks:
            for task in user_tasks:
                await utils.telegram_api.send_message(
                    telegram_id=user.telegram_id,
                    message=await translation.new_task_message(task=task),
                )

            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, tasks=new_user_tasks
            )
    else:
        logger.warning(
            f"\nOn user tasks synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {tasks_resp[1]}"
        )

    # Обработка списка повесток дня
    if agenda_resp[0]:
        old_user_agenda = json.loads(user.agenda)
        old_user_agenda_all_false = []
        for item in old_user_agenda:
            item_copy = copy.deepcopy(item)
            item_copy["notified"] = False
            old_user_agenda_all_false.append(item_copy)

        new_user_agenda = agenda_resp[1]

        user_agenda = [
            item for item in new_user_agenda if item not in old_user_agenda_all_false
        ]

        if user_agenda:
            today = datetime.datetime.now(settings.timezone).date()
            tomorrow = today + datetime.timedelta(days=1)

            day = tomorrow.strftime("%d.%m.%Y")
            for agenda_ in user_agenda:
                await utils.telegram_api.send_message(
                    telegram_id=user.telegram_id,
                    message=await translation.new_agenda_message(agenda=agenda_),
                )
                if agenda_["date"] == day:
                    agenda_["notified"] = True

                old_user_agenda.append(agenda_)

            sorted_user_agenda = sorted(old_user_agenda, key=custom_key)

            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, agenda=sorted_user_agenda
            )

        if old_user_agenda:
            today = datetime.datetime.now(settings.timezone).date()
            tomorrow = today + datetime.timedelta(days=1)

            day = tomorrow.strftime("%d.%m.%Y")
            if (
                agenda_tomorrow := methods.find_dict_by_key_value(
                    input_list=old_user_agenda, key="date", value=day
                )
            ) is not None:
                for agenda_ in agenda_tomorrow:
                    if agenda_["notified"]:
                        continue
                    await utils.telegram_api.send_message(
                        telegram_id=user.telegram_id,
                        message=await translation.next_day_agenda_message(
                            agenda=agenda_
                        ),
                    )

                    index = old_user_agenda.index(agenda_)
                    agenda_["notified"] = True

                    old_user_agenda[index] = agenda_

                sorted_user_agenda = sorted(old_user_agenda, key=custom_key)

                await database.update_user_by_telegram_id(
                    telegram_id=user.telegram_id, agenda=sorted_user_agenda
                )
            else:
                if new_user_agenda:
                    old_user_agenda_all_false = []
                    for item in old_user_agenda:
                        item_copy = copy.deepcopy(item)
                        item_copy["notified"] = False
                        old_user_agenda_all_false.append(item_copy)

                    sorted_old_user_agenda = sorted(
                        old_user_agenda_all_false, key=custom_key
                    )
                    sorted_new_user_agenda = sorted(new_user_agenda, key=custom_key)

                    if sorted_old_user_agenda != sorted_new_user_agenda:
                        await database.update_user_by_telegram_id(
                            telegram_id=user.telegram_id, agenda=sorted_new_user_agenda
                        )
    else:
        logger.warning(
            f"\nOn user agenda synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {agenda_resp[1]}"
        )

    # Обработка изменений в данных пользователя
    if user_data_resp:
        old_user_data = json.loads(user.user_data)

        if old_user_data != user_data_resp:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, user_data=user_data_resp
            )
    else:
        logger.warning(
            f"\nOn user data synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nResponse: {user_data_resp}"
        )

    # Обработка списка расписания
    if schedule_resp[0]:
        new_user_schedule = schedule_resp[1]
        old_user_schedule = json.loads(user.schedule)

        if old_user_schedule != new_user_schedule:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, schedule=new_user_schedule
            )
    else:
        logger.warning(
            f"\nOn user schedule synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {agenda_resp[1]}"
        )

    #  Обработка сообщений
    if messenger_resp[0]:
        messages = messenger_resp[1]

        user_messages = json.loads(user.messages)
        changed = False

        for message in messages:
            if not message["files"] or not (
                await possible_message(user_messages=user_messages, message=message)
            ):
                continue

            changed = True
            first_passed = False

            for file_id in message["files"][0]:
                download_resp = await methods.download_file_with_url(
                    url=await methods.generate_linc_for_message_download(id_=file_id),
                    PHPSESSID_cookie=auth_resp[1],
                    messenger_cookie=auth_resp[2],
                )

                if not download_resp[0]:
                    continue

                file_path = download_resp[1]

                message = await translation.new_circular_message()

                if not first_passed:
                    await telegram_api.send_message(
                        telegram_id=user.telegram_id, message=message
                    )
                    first_passed = True

                finished = False
                attempts = 0

                while not finished and attempts < 3:
                    try:
                        await telegram_api.send_file(
                            telegram_id=user.telegram_id, file_path=file_path
                        )
                        finished = True
                    except telegram.error.TimedOut:
                        attempts += 1

                split_file_path = file_path.split("/")

                folder_path = f"{split_file_path[0]}/{split_file_path[1]}"

                await methods.delete_folder(folder_path=folder_path)

        if changed:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, messages=messages
            )

    else:
        logger.warning(
            f"\nOn user messages synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {messenger_resp[1]}"
        )

    #  Обработка пропусков в школе
    if absence_resp[0]:
        user_absence: list = json.loads(user.absence)
        absence_list = absence_resp[1]

        if absence_list != user_absence:
            for absence_item in absence_list:
                if absence_item in user_absence:
                    continue

                message = await translation.new_absence(absence_item)

                await telegram_api.send_message(
                    telegram_id=user.telegram_id, message=message
                )

            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, absence=absence_list
            )
    else:
        logger.warning(
            f"\nOn user absence synchronization error!"
            f"\nTelegram ID: {user.telegram_id}"
            f"\nReport file: {absence_resp[1]}"
        )


async def sync_all_users() -> None:
    logger.debug("Start all users synchronization!")
    users = await database.get_all_users()

    if not users:
        return

    tasks_ = []

    for user in users:
        tasks_.append(asyncio.create_task(sync_user(user)))

    await asyncio.gather(*tasks_)


async def keyboard_sync():
    with open("config/update.json", "r") as file:
        data = json.load(file)
        if not data["button_update"]:
            file.close()
            return

    data["button_update"] = False

    with open("config/update.json", "w") as file:
        json.dump(data, file)
        file.close()

    users = await database.get_all_users()

    if not users:
        return

    for user in users:
        try:
            user_settings = json.loads(user.user_settings)
            language = user_settings["language"]
            translation = formaters.LanguageFormations(language=language)
            await translation.setup()
            await telegram_api.send_message(
                user.telegram_id,
                message="🎉 Minor update\n"
                "Il bot ora ha la possibilità di visualizzare le assenze. Sebbene non sia molto utile, "
                "questo aggiornamento aspetta da molto tempo. Invio di nuovi pulsanti per il menu!",
                markup=await bot_menu.main_menu(language=language),
            )
        except:
            logger.error(traceback.format_exc())
            continue


async def update_sync():
    with open("config/update.json", "r") as file:
        data = json.load(file)
        if not data["update"]:
            file.close()
            return

    data["update"] = False

    with open("config/update.json", "w") as file:
        json.dump(data, file)
        file.close()

    users = await database.get_all_users()

    for user in users:
        response = await auth_functions.fast_auth(user=user.login, password=user.password)

        if not response[0]:
            logger.warning("Failed to authorize user")

        PHPSESSID_cookie = response[1]
        messenger_cookie = response[2]

        user_data = await auth_functions.get_user_data(messenger_cookie, PHPSESSID_cookie)
        task_list = await tasks.get_user_tasks(user=user.login, password=user.password)
        user_schedule = await schedule.get_user_schedule(user=user.login, password=user.password)
        user_marks = await marks.get_user_marks(user=user.login, password=user.password)
        user_agenda = await agenda.get_user_agenda(user=user.login, password=user.password)
        user_absence = await absence.get_user_absence(user=user.login, password=user.password)

        if task_list[0]:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, tasks=task_list[1]
            )
        if user_schedule[0]:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, schedule=user_schedule[1]
            )
        if user_marks[0]:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, marks=user_marks[1]
            )
        if user_agenda[0]:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, agenda=user_agenda[1]
            )
        if user_data:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, user_data=user_data
            )
        if user_absence[0]:
            await database.update_user_by_telegram_id(
                telegram_id=user.telegram_id, absence=user_absence[1]
            )


def possible_synchronization() -> bool:
    current_time = datetime.datetime.now(tz=settings.timezone).time()

    impossible_period_start = current_time.replace(hour=23, minute=49, second=0)
    impossible_period_end = current_time.replace(hour=23, minute=53, second=0)

    possible = True

    if impossible_period_start < current_time <= impossible_period_end:
        possible = False

    return possible


async def main_sync():
    await update_sync()
    await keyboard_sync()
    while True:
        try:
            if possible_synchronization():
                await sync_all_users()
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(
                await formaters.generate_error_message(
                    text="Sync ERROR", error_message=str(e)
                )
            )
