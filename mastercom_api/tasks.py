import re
import traceback
from typing import Union, Any

import aiohttp
import bs4
from bs4 import BeautifulSoup

from config import settings
from formaters import generate_error_message
from logs.log import log_with_random_path
from mastercom_api import auth_functions

italian_month = {
    "gennaio": ".01",
    "febbraio": ".02",
    "marzo": ".03",
    "aprile": ".04",
    "maggio": ".05",
    "giugno": ".06",
    "luglio": ".07",
    "agosto": ".08",
    "settembre": ".09",
    "ottobre": ".10",
    "novembre": ".11",
    "dicembre": ".12",
}


async def get_exercises_data(
    result: bs4.PageElement, current_date: str, subjects_list: list
) -> Union[bool, Any]:
    subjects = result.find_all(name="td", class_="border-left border-gray padding-8")

    for subject in subjects:
        subject_name_object = subject.find_next(name="strong")
        subject_name = subject_name_object.text
        task_objects = subject.find_all(
            name="div",
            class_="padding-small border-left-2 margin-bottom-small break-word border-amber",
        )

        for task_object in task_objects:
            task_text = task_object.get_text(strip=True)
            if "Da fare" in task_text:
                task = task_text.split("Da fare")[0].replace("\n", " ")
            else:
                task = task_text.split("Fatto")[0].replace("\n", " ")
            if not task:
                continue
            professor_info_object = task_object.find_next(
                name="i", class_="text-gray small"
            )
            professor_name = (
                professor_info_object.text.replace("(", "")
                .replace(")", "")
                .split(" - ")[1]
            )
            lesson_time = (
                professor_info_object.text.replace("(", "")
                .replace(")", "")
                .split(" - ")[0]
            )

            subjects_list.append(
                {
                    "subject_name": subject_name,
                    "task": task,
                    "date": current_date,
                    "time": lesson_time,
                    "professor_name": professor_name,
                }
            )

    return subjects_list


async def get_user_tasks(user: str, password: str):
    resp = await auth_functions.fast_auth(password=password, user=user)
    if not resp[0]:
        return False, await log_with_random_path(
            await generate_error_message(
                resp=resp,
            )
        )

    PHPSESSID_cookie = resp[1]
    messenger_cookie = resp[2]
    current_key = resp[3]

    if not (
        user_data := await auth_functions.get_user_data(
            messenger_cookie=messenger_cookie, PHPSESSID_cookie=PHPSESSID_cookie
        )
    ):
        return False, await log_with_random_path(
            await generate_error_message(user_data=user_data, resp=resp)
        )
    user_id = None
    try:
        user_id = user_data["results"]["properties"]["code"]
    except KeyError:
        return False, await log_with_random_path(
            await generate_error_message(user_id=user_id, user_data=user_data)
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url="https://righi-fc.registroelettronico.com/mastercom/index.php",
            headers={
                "Cookie": f"PHPSESSID={PHPSESSID_cookie}; messenger={messenger_cookie}"
            },
            data={
                "form_stato": "studente",
                "stato_principale": "argomenti-compiti",
                "stato_secondario": "",
                "permission": "",
                "operazione": "",
                "current_user": f"{user_id}",
                "current_key": current_key,
                "from_app": "",
                "header": "SI",
            },
        ) as resp:
            if resp.status != 200:
                return False, await log_with_random_path(
                    await generate_error_message(
                        PHPSESSID_cookie=PHPSESSID_cookie,
                        messenger_cookie=messenger_cookie,
                        user_data=user_data,
                        user_id=user_id,
                        current_key=current_key,
                        resp_status=resp.status,
                    )
                )
            else:
                try:
                    soup = BeautifulSoup(await resp.text(), features="html.parser")
                    results = soup.find_all(
                        name="tr", class_="border-bottom border-gray"
                    )

                    subjects_list = []
                    current_date = None

                    for result in results:
                        if not result:
                            continue

                        try:
                            date_strong = result.find_next(name="strong")

                            cleaned_date = re.sub(
                                r"(\d)([a-zA-Z])",
                                r"\1 \2",
                                date_strong.text.replace(" ", "")
                                .replace("\n", "")
                                .replace("\t", ""),
                            )

                            if cleaned_date is None:
                                continue

                            split_date = cleaned_date.split(" ")

                            if len(split_date) < 2:
                                raise TypeError

                            month = italian_month[split_date[1]]

                            date = f"{int(split_date[0]):02}{month}"

                            if not date:
                                raise TypeError

                            current_date = (
                                date
                                + f".{settings.current_school_start_year if int(month.replace('.', '')) > 8 else settings.current_school_start_year + 1}"
                            )

                            # Начинаем искать урок из бокса с датой
                            subjects_list = await get_exercises_data(
                                result=result,
                                current_date=current_date,
                                subjects_list=subjects_list,
                            )

                        except TypeError:
                            # Ищем урок без бокса с датой
                            subjects_list = await get_exercises_data(
                                result=result,
                                current_date=current_date,
                                subjects_list=subjects_list,
                            )
                    return True, subjects_list
                except Exception:
                    return False, await log_with_random_path(
                        await generate_error_message(
                            error_message=traceback.format_exc(),
                            PHPSESSID_cookie=PHPSESSID_cookie,
                            messenger_cookie=messenger_cookie,
                            user_data=user_data,
                            user_id=user_id,
                            current_key=current_key,
                            resp_status=resp.status,
                            soup=soup,
                            results=results,
                            subjects_list=subjects_list,
                            current_date=current_date,
                            result=result,
                            date_strong=date_strong,
                            cleaned_date=cleaned_date,
                            split_date=split_date,
                            date=date,
                        )
                    )
