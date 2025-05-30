from typing import Union, Any

import aiohttp
from bs4 import BeautifulSoup

from formaters import generate_error_message
from logs.log import log_with_random_path
from mastercom_api import auth_functions


async def get_user_absence(user: str, password: str) -> Union[bool, Any]:
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
    current_user_id = None
    try:
        current_user_id = user_data["results"]["properties"]["code"]
    except KeyError:
        return False, await log_with_random_path(
            await generate_error_message(user_id=current_user_id, user_data=user_data)
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url="https://righi-fc.registroelettronico.com/mastercom/index.php",
            headers={
                "Cookie": f"PHPSESSID={PHPSESSID_cookie}; messenger={messenger_cookie}"
            },
            data={
                "form_stato": "studente",
                "stato_principale": "assenze",
                "stato_secondario": "",
                "permission": "",
                "operazione": "",
                "current_user": f"{current_user_id}",
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
                        user_id=current_user_id,
                        current_key=current_key,
                        resp_status=resp.status,
                    )
                )
            absence_list = []
            try:
                soup = BeautifulSoup(await resp.text(), features="html.parser")
                results = soup.find_all(name="tr", **{"data-giustificata": "0"})

                for result in results:
                    date: str = (result["data-date"]).replace("-", ".")

                    td_objects = result.find_all("td", class_=False)
                    if len(td_objects) < 3:
                        continue

                    description_object = td_objects[2]

                    split_description = (
                        description_object.get_text(strip=True)
                        .replace("Da giustificare", "")
                        .replace("\n", "")
                        .split(" ")
                    )
                    description = " ".join(word for word in split_description if word)

                    absence_list.append({"date": date, "description": description})
                return True, absence_list
            except Exception:
                return False, await log_with_random_path(
                    await generate_error_message(
                        PHPSESSID_cookie=PHPSESSID_cookie,
                        messenger_cookie=messenger_cookie,
                        user_data=user_data,
                    )
                )
