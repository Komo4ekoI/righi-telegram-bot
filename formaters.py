import datetime
import json

import aiofiles

from config import settings

months = {
    "gennaio": "01",
    "febbraio": "02",
    "marzo": "03",
    "aprile": "04",
    "maggio": "05",
    "giugno": "06",
    "luglio": "07",
    "agosto": "08",
    "settembre": "09",
    "ottobre": "10",
    "novembre": "11",
    "dicembre": "12",
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

available_days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


async def generate_error_message(
    text: str = None, error_message: str = None, **kwargs
) -> str:
    message = f"\n{'*' * 50}\n\n"
    if text is not None:
        message += f"Description: {text}\n"
        message += "-" * 50 + "\n"

    if error_message is not None:
        message += f"{error_message}\n"
        message += "-" * 50 + "\n"

    for key, value in kwargs.items():
        message += f"{key}: {value}\n"
        message += "-" * 50 + "\n"

    message += "*" * 50

    return message


class LanguageFormations:
    def __init__(self, language: str):
        self.language = language
        self.translation = {}

    MAX_LESSON_NAME_LENGHT = 16

    lesson_start_numbers = {
        "08:05": "1️⃣",
        "09:05": "2️⃣",
        "10:05": "3️⃣",
        "11:05": "4️⃣",
        "12:05": "5️⃣",
    }

    numbers_emoji = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
    }

    dots = "..."

    async def setup(self):
        async with aiofiles.open(
            f"utils/translate/{self.language}.json", "r", encoding="utf-8"
        ) as file:
            content = await file.read()
            self.translation = json.loads(content)

    async def new_mark_message(self, mark: dict) -> str:
        message = "📊"
        if mark["notification"]:
            message += f"{self.translation['NEW_POSITIVE_NOTOFICATION'] if mark['positive_notification'] else self.translation['NEW_NEGATIVE_NOTOFICATION']}\n"
            message += f"{self.translation['SUBJECT_NAME']}: {mark['subject']}\n"
        else:
            message += f"{self.translation['NEW_MARK']}\n"
            message += f"{self.translation['SUBJECT_NAME']}: {mark['subject']}\n"
            message += f"{self.translation['MARK']}: {mark['mark']}\n"
        message += (
            f"{self.translation['DESCRIPTION']}: {mark['mark_description']}"
            if mark["mark_description"]
            else ""
        )
        return message

    async def new_task_message(self, task: dict) -> str:
        message = ""

        day, month, _ = task["date"].split(".")
        today = datetime.datetime.now(settings.timezone).date()
        tomorrow = today + datetime.timedelta(days=1)

        message += f"\U0001F4DA{self.translation['NEW_TASK']}"
        if day.zfill(2) == str(tomorrow.day).zfill(2) and month.zfill(2) == str(
            tomorrow.month
        ).zfill(2):
            message += f"{self.translation['TOMORROW']}\n"
        else:
            message += f"<b>{day} {self.translation[month]}</b>\n"

        message += f"{self.translation['SUBJECT_NAME']}: {task['subject_name']}\n"
        message += f"{self.translation['TASK']}: {task['task']}"

        return message

    async def new_agenda_message(self, agenda: dict) -> str:
        message = ""

        day, month, _ = agenda["date"].split(".")
        today = datetime.datetime.now(settings.timezone).date()
        tomorrow = today + datetime.timedelta(days=1)

        message += f"\U0001F4CB{self.translation['NEW_AGENDA']}"
        if day.zfill(2) == str(tomorrow.day).zfill(2) and month.zfill(2) == str(
            tomorrow.month
        ).zfill(2):
            message += f"{self.translation['TOMORROW']}"
        else:
            message += f"<b>{day} {self.translation[month]}</b>"

        message += (
            f"\n{self.translation['NAME']}: {agenda['name']}" if agenda["name"] else ""
        )
        message += (
            f"\n{self.translation['DESCRIPTION']}: {agenda['description']}"
            if agenda["description"]
            else ""
        )
        message += f"\n{self.translation['TIME']}: {agenda['start_time']} - {agenda['end_time']}"

        return message

    async def next_day_agenda_message(self, agenda: dict) -> str:
        message = ""

        message += f"\u203C{self.translation['TOMORROW_AGENDA']}"
        message += (
            f"\n{self.translation['NAME']}: {agenda['name']}" if agenda["name"] else ""
        )
        message += (
            f"\n{self.translation['DESCRIPTION']}: {agenda['description']}"
            if agenda["description"]
            else ""
        )
        message += f"\n{self.translation['TIME']}: {agenda['start_time']} - {agenda['end_time']}\n"
        message += f"{self.translation['PROFESSOR_NAME']}: {agenda['professor_name']}"

        return message

    async def user_not_found(self) -> str:
        message = ""

        message += f"{self.translation['ERROR']}\n"
        message += f"{self.translation['USER_NOT_FOUND']}"

        return message

    async def day_schedule(self, lessons: list) -> str:
        message = ""
        _, month, day = lessons[0]["data_inizio_tradotta_iso"].split("-")
        upped_name = lessons[0]["giorno_tradotto"].upper().replace("Ì", "")
        message += f"<b>{self.translation[upped_name].upper()}: {day} {self.translation[month]}</b>"

        for lesson in lessons:
            message += (
                f"\n{self.lesson_start_numbers[lesson['ora_inizio_tradotta']]} "
                f"{lesson['ora_inizio_tradotta']} - {lesson['ora_fine_tradotta']} | "
                f"{lesson['nome_materia_sito'][:self.MAX_LESSON_NAME_LENGHT]}"
                f"{self.dots if len(lesson['nome_materia_sito']) >= self.MAX_LESSON_NAME_LENGHT else ''}"
            )

        return message

    async def welcome_message(self, user_data: dict) -> str:
        message = ""

        try:
            name = user_data["results"]["properties"]["name"]
        except:
            name = "unknown name"

        message += f"<b>{self.translation['HELLO']} {name}</b>\U0001F389\n\n"
        message += f"{self.translation['SUCCESSFUL_REGISTRATION']}"

        return message

    async def agenda_message(self, agenda_list: list) -> str:
        message = ""
        emoji_index = 1
        split_date = agenda_list[0]["date"].split(".")
        message += (
            f"<b>{split_date[0].lstrip('0')} {self.translation[split_date[1]]}</b>\n"
        )
        for agenda in agenda_list:
            message += f"{self.numbers_emoji[emoji_index]}"
            message += (
                f"{self.translation['NAME']}: {agenda['name']}\n"
                if agenda["name"]
                else ""
            )
            message += (
                f"{self.translation['DESCRIPTION']}: {agenda['description']}\n"
                if agenda["description"]
                else ""
            )
            message += f"{self.translation['TIME']}: {agenda['start_time']} - {agenda['end_time']}\n"
            message += (
                f"{self.translation['PROFESSOR_NAME']}: {agenda['professor_name']}\n\n"
            )
            emoji_index += 1

        return message

    async def day_tasks(self, tasks: list) -> str:
        emoji_index = 1
        message = ""
        tasks = list(reversed(tasks))
        split_date = tasks[0]["date"].split(".")

        message += (
            f"<b>{split_date[0].lstrip('0')} {self.translation[split_date[1]]}</b>"
        )
        finished = False
        while not finished:
            task_ = tasks[0]
            subject_tasks = [
                task for task in tasks if task_["subject_name"] == task["subject_name"]
            ]

            message += (
                f"\n{self.numbers_emoji[emoji_index]}<b>{task_['subject_name'] if len(task_['subject_name']) < self.MAX_LESSON_NAME_LENGHT else task_['subject_name'][:self.MAX_LESSON_NAME_LENGHT] + self.dots}</b>"
            ) + "<b>:</b>"

            subject_tasks_len = len(subject_tasks)
            for task in subject_tasks:
                message += f"\n{self.translation['TASK']}: {task['task']}\n"
                message += f"{self.translation['ENTER']}: {task['time']}"
                tasks.remove(task)
                if subject_tasks.index(task) + 1 == subject_tasks_len and tasks:
                    message += "\n"

            emoji_index += 1
            if not tasks:
                finished = True

        return message

    async def marks_message(self, marks_list: list) -> str:
        message = ""
        emoji_index = 1
        for mark in marks_list:
            message += f"{self.numbers_emoji[emoji_index]}"

            split_date = mark["date"].split(".")

            if mark["notification"]:
                message += f"{self.translation['POSITIVE_NOTOFICATION'] if mark['positive_notification'] else self.translation['NEGATIVE_NOTOFICATION']}"
                message += f"<b>{split_date[0]} {self.translation[split_date[1]]}</b>\n"
                message += f"{self.translation['SUBJECT_NAME']}: {mark['subject']}\n"
            else:
                message += f"{self.translation['UPPED_MARK']}<b>{split_date[0]} {self.translation[split_date[1]]}</b>\n"
                message += f"{self.translation['SUBJECT_NAME']}: {mark['subject']}\n"
                message += f"{self.translation['MARK']}: {mark['mark']}\n"
            message += (
                (f"{self.translation['DESCRIPTION']}: {mark['mark_description']}\n")
                if mark["mark_description"]
                else ""
            )
            emoji_index += 1

        return message

    async def new_circular_message(self) -> str:
        message = ""

        message += f"{self.translation['NEW_CIRCULAR']}\n"

        return message

    async def absence_message(self, absence_list: list) -> str:
        message = ""
        number = 1
        for absence in absence_list:
            year, month, day = absence["date"].split(".")
            message += f"<b>{self.numbers_emoji[number]} {int(day)} {self.translation[month]} {year}</b>\n"
            message += f"{self.translation['REASON']}: {absence['description']}\n\n"
            number += 1

        return message

    async def new_absence(self, absence_data: dict) -> str:
        _, month, day = absence_data["date"].split(".")
        message = f"{self.translation['NEW_ABSENCE']}{int(day)} {self.translation[month].upper()}\n"
        message += f"{self.translation['REASON']}: {absence_data['description']}"

        return message
