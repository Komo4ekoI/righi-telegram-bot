from typing import Union, Any

import aiohttp
from bs4 import BeautifulSoup

from config import settings
from formaters import generate_error_message
from logs.log import log_with_random_path
from mastercom_api import auth_functions

short_italian_month = {
    "gen": ".01",
    "feb": ".02",
    "mar": ".03",
    "apr": ".04",
    "mag": ".05",
    "giu": ".06",
    "lug": ".07",
    "ago": ".08",
    "set": ".09",
    "ott": ".10",
    "nov": ".11",
    "dic": ".12",
}


async def get_user_agenda(user: str, password: str) -> Union[bool, Any]:
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
                "stato_principale": "agenda",
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
                agenda_list = []
                try:
                    soup = BeautifulSoup(await resp.text(), features="html.parser")
                    results = soup.find_all(
                        name="tr", class_="border-bottom border-gray"
                    )
                    for result in results:
                        if not result:
                            continue

                        date_object = result.find_next(name="td", class_="center").find(
                            name="strong", class_=False
                        )
                        split_date = (
                            date_object.get_text(strip=True)
                            .replace(" ", "")
                            .replace("\n", " ")
                            .split(" ")
                        )
                        date = split_date[0] + short_italian_month[split_date[1]]

                        if (
                            int(short_italian_month[split_date[1]].replace(".", ""))
                            >= 8
                        ):
                            date += f".{settings.current_school_start_year}"
                        else:
                            date += f".{settings.current_school_start_year + 1}"

                        data_objects = result.find_all(
                            name="div",
                            class_="padding-small border-left-2 margin-bottom border-green",
                        )

                        for data_object in data_objects:
                            if not data_object:
                                continue

                            time_text = data_object.find_next(
                                name="div", class_="right right-align"
                            ).get_text(strip=True)
                            start_time = time_text[:5]
                            end_time = time_text[5:]

                            name = data_object.find_next(name="strong").get_text(
                                strip=True
                            )

                            professor_name = (
                                data_object.find_next(
                                    name="i", class_="text-gray small"
                                )
                                .get_text(strip=True)
                                .replace("(", "")
                                .replace(")", "")
                            )

                            description = (
                                data_object.get_text(strip=True)
                                .replace("(" + professor_name + ")", "")
                                .replace(start_time, "")
                                .replace(end_time, "")
                                .replace(name, "")
                            )

                            agenda_list.append(
                                {
                                    "name": name,
                                    "description": description,
                                    "date": date,
                                    "start_time": start_time,
                                    "end_time": end_time,
                                    "professor_name": professor_name,
                                    "notified": False,
                                }
                            )
                    return True, list(reversed(agenda_list))
                except Exception:
                    return False, await log_with_random_path(
                        await generate_error_message(
                            PHPSESSID_cookie=PHPSESSID_cookie,
                            messenger_cookie=messenger_cookie,
                            user_data=user_data,
                            user_id=user_id,
                            current_key=current_key,
                            resp_status=resp.status,
                            results=results,
                            result=result,
                            date_object=date_object,
                            split_date=split_date,
                            date=date,
                            data_object=data_object,
                            time_text=time_text,
                            start_time=start_time,
                            end_time=end_time,
                            name=name,
                            description=description,
                            professor_name=professor_name,
                            agenda_list=agenda_list,
                        )
                    )
