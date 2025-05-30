from typing import Union, Any

import aiohttp

from formaters import generate_error_message
from logs.log import log_with_random_path


async def get_user_messages(
    PHPSESSID_cookie: str, messenger_cookie: str
) -> Union[bool, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url="https://righi-fc.registroelettronico.com/messenger/1.0/messages?_dc=20394&page=1&start=0&limit=999999",
            headers={
                "Cookie": f"PHPSESSID={PHPSESSID_cookie}; messenger={messenger_cookie}"
            },
            data={"_dc": "20394", "page": "1", "start": "0", "limit": "999999"},
        ) as resp:
            if resp.status != 200 or not (resp_json := await resp.json())["success"]:
                return False, await log_with_random_path(
                    await log_with_random_path(
                        await generate_error_message(
                            PHPSESSID_cookie=PHPSESSID_cookie,
                            messenger_cookie=messenger_cookie,
                            resp_status=resp.status,
                        )
                    )
                )
            else:
                try:
                    results = resp_json["results"]
                    return True, results
                except:
                    return False, await log_with_random_path(
                        await log_with_random_path(
                            await generate_error_message(
                                PHPSESSID_cookie=PHPSESSID_cookie,
                                messenger_cookie=messenger_cookie,
                                resp_status=resp.status,
                                resp_json=resp_json,
                                results=results,
                            )
                        )
                    )
