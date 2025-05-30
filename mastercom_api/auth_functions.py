import logging
import re

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def get_user_data(messenger_cookie: str, PHPSESSID_cookie: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url="https://righi-fc.registroelettronico.com/messenger/1.0/authentication",
            headers={
                "Cookie": f"messenger={messenger_cookie}; PHPSESSID={PHPSESSID_cookie}"
            },
        ) as resp:
            if resp.status != 200 or not (resp_json := await resp.json())["success"]:
                return False
            else:
                return resp_json


async def get_PHPSESSID_cookie():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://righi-fc.registroelettronico.com/mastercom/"
        ) as resp:
            match = re.search(r"PHPSESSID=([^;]+)", str(resp.cookies["PHPSESSID"]))
            if match:
                return match.group(1)
            else:
                return False


async def get_messenger_cookie(PHPSESSID_cookie: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://righi-fc.registroelettronico.com/messenger/1.0/authentication",
            headers={"Cookie": f"PHPSESSID={PHPSESSID_cookie}"},
        ) as resp:
            match = re.search(r"messenger=([^;]+)", str(resp.cookies["messenger"]))
            if match:
                return match.group(1)
            else:
                return False


async def authorization(PHPSESSID_cookie: str, messenger_cookie: str, current_key: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=f"https://righi-fc.registroelettronico.com/messenger/1.0/login/{current_key}",
            headers={
                "Cookie": f"PHPSESSID={PHPSESSID_cookie}; messenger={messenger_cookie}"
            },
        ) as resp:
            if resp.status != 200:
                return False
            else:
                return True


async def get_current_key(
    PHPSESSID_cookie: str, messenger_cookie: str, password: str, user: str
):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url="https://righi-fc.registroelettronico.com/mastercom/index.php",
            headers={
                "Cookie": f"PHPSESSID={PHPSESSID_cookie}; messenger={messenger_cookie}"
            },
            data={"user": user, "password_user": password, "form_login": "true"},
        ) as resp:
            if resp.status != 200:
                return False
            else:
                soup = BeautifulSoup(await resp.text(), "html.parser")
                current_key = soup.find("input", {"id": "current_key"})["value"]
                return current_key if current_key else None


async def fast_auth(password: str = None, user: str = None, current_key: str = None):
    if current_key is None and password is None and user is None:
        return False, None, None, None

    if not (PHPSESSID_cookie := await get_PHPSESSID_cookie()):
        return False, None, None, None

    if not (
        messenger_cookie := await get_messenger_cookie(
            PHPSESSID_cookie=PHPSESSID_cookie
        )
    ):
        return False, None, None, None

    if current_key is None:
        current_key = await get_current_key(
            PHPSESSID_cookie=PHPSESSID_cookie,
            messenger_cookie=messenger_cookie,
            password=password,
            user=user,
        )
    status = await authorization(
        PHPSESSID_cookie=PHPSESSID_cookie,
        messenger_cookie=messenger_cookie,
        current_key=current_key,
    )
    if not status:
        logger.warning(f"\nStatus: {status}")
        return False, None, None, None
    return True, PHPSESSID_cookie, messenger_cookie, current_key
