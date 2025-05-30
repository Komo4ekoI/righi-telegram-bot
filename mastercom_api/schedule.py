import json
import re
import traceback
from typing import Any, Union

import aiohttp

from formaters import generate_error_message
from logs.log import log_with_random_path
from mastercom_api import auth_functions


async def get_user_schedule(
    user: str, password: str, limit: int = None, daily: bool = False
) -> Union[bool, Any]:
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
                "stato_principale": "orario",
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
                    await log_with_random_path(
                        await generate_error_message(
                            limit=limit,
                            daily=daily,
                            PHPSESSID_cookie=PHPSESSID_cookie,
                            messenger_cookie=messenger_cookie,
                            user_data=user_data,
                            user_id=user_id,
                            resp_status=resp.status,
                        )
                    )
                )
            else:
                pattern = re.compile(r"JSON\.parse\('(.+?)'\);")
                matches = pattern.search(await resp.text())
                if matches:
                    try:
                        schedule_json = json.loads(matches.group(1))
                        if limit is not None:
                            return (
                                True,
                                schedule_json[
                                    f"{'elenco_ore_giornata' if daily else 'elenco_ore_totale'}"
                                ][:limit],
                            )
                        return (
                            True,
                            schedule_json[
                                f"{'elenco_ore_giornata' if daily else 'elenco_ore_totale'}"
                            ],
                        )
                    except KeyError:
                        return False, await log_with_random_path(
                            await generate_error_message(
                                error_message=traceback.format_exc()
                            )
                        )
                else:
                    return False, await log_with_random_path(
                        await log_with_random_path(
                            await generate_error_message(
                                limit=limit,
                                daily=daily,
                                PHPSESSID_cookie=PHPSESSID_cookie,
                                messenger_cookie=messenger_cookie,
                                user_data=user_data,
                                user_id=user_id,
                                resp_status=resp.status,
                                pattern=pattern,
                                matches=matches,
                            )
                        )
                    )
