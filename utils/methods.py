import os
import random
import shutil
import string
from typing import Any

import aiofiles
import aiohttp
from telegram import ReplyKeyboardRemove

import formaters
from formaters import generate_error_message
from logs.log import log_with_random_path
from utils import database
from utils import telegram_api


def find_dict_by_key_value(input_list: list, key: str, value: Any) -> list | None:
    items = []
    for item in input_list:
        if key in item and item[key] == value:
            items.append(item)

    if items:
        return items
    return None


async def delete_user_data(telegram_id: int) -> None:
    translation = formaters.LanguageFormations(language="it")
    await translation.setup()
    await database.delete_user(telegram_id=telegram_id)
    await telegram_api.send_message(
        telegram_id=telegram_id,
        message=translation.translation["USER_NOT_FOUND"],
        markup=ReplyKeyboardRemove(),
    )


async def generate_linc_for_message_download(id_: str) -> str:
    return f"https://righi-fc.registroelettronico.com/messenger/1.0/messages/{id_}/raw"


async def download_file_with_url(
    url: str, PHPSESSID_cookie: str, messenger_cookie: str
):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=url,
            headers={
                "Cookie": f"PHPSESSID={PHPSESSID_cookie}; messenger={messenger_cookie}"
            },
        ) as resp:
            if resp.status != 200:
                return False, await log_with_random_path(
                    await log_with_random_path(
                        await generate_error_message(
                            link=url,
                            PHPSESSID_cookie=PHPSESSID_cookie,
                            messenger_cookie=messenger_cookie,
                            resp_status=resp.status,
                        )
                    )
                )
            else:
                content_disposition = resp.headers.get("content-disposition")
                random_folder = "".join(
                    random.choice(string.ascii_letters + string.digits)
                    for _ in range(10)
                )

                os.mkdir(f"temporary/{random_folder}")

                if content_disposition:
                    filename = (
                        f"temporary/{random_folder}/"
                        + content_disposition.split("filename=")[1]
                    )
                else:
                    random_filename = "".join(
                        random.choice(string.ascii_letters + string.digits)
                        for _ in range(10)
                    )
                    filename = f"temporary/{random_folder}/{random_filename}.pdf"

                filename = filename.replace('"', "")
                try:
                    async with aiofiles.open(filename, "+wb") as pdf_file:
                        content = await resp.read()
                        await pdf_file.write(content)
                        await pdf_file.close()
                except:
                    return False, await log_with_random_path(
                        await log_with_random_path(
                            await generate_error_message(
                                link=url,
                                PHPSESSID_cookie=PHPSESSID_cookie,
                                messenger_cookie=messenger_cookie,
                                resp_status=resp.status,
                                filename=filename,
                                content=content,
                            )
                        )
                    )

                return True, filename


async def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)


async def delete_folder(folder_path: str):
    try:
        shutil.rmtree(folder_path)
    except OSError:
        return
