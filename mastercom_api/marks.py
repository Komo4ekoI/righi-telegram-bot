import logging
import traceback

import aiohttp
from bs4 import BeautifulSoup

from formaters import generate_error_message
from logs.log import log_with_random_path
from mastercom_api import auth_functions

logger = logging.getLogger(__name__)


async def get_user_marks(
    user: str,
    password: str,
    marks_limit: int = None,
):
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
                "stato_principale": "voti",
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
                        user_id=user_id,
                        current_key=current_key,
                        user_data=user_data,
                        status=resp.status,
                    )
                )
            else:
                try:
                    soup = BeautifulSoup(await resp.text(), features="html.parser")
                    marks_object = soup.find_all(name="td", class_="cell-middle center")

                    marks_list = []

                    marks_count = 0

                    for mark_object in marks_object:
                        notification = False
                        positive_notification = False

                        if not mark_object:
                            continue

                        if not (
                            mark := mark_object.find_next(name="strong").get_text(
                                strip=True
                            )
                        ):
                            continue

                        center_object = mark_object.find_next(
                            name="td", class_="center"
                        )
                        if not center_object:
                            continue

                        if not (
                            date := center_object.find_next(name="i")
                            .get_text(strip=True)
                            .replace("/", ".")
                        ):
                            continue

                        if not (
                            received_for := center_object.find_next(
                                name="div",
                                class_=True,
                            )
                            .find_next(name="i")
                            .get_text(strip=True)
                        ):
                            continue

                        if not (
                            subject_object := mark_object.find_next(
                                name="td", class_=False
                            )
                        ):
                            continue

                        subject = subject_object.find_next(name="strong").get_text(
                            strip=True
                        )

                        type_object = subject_object.find(name="span", class_="small")
                        if type_object:
                            type_ = type_object.get_text(strip=True)
                            if "Annotazione" in type_ and "positiva" in type_:
                                notification = True
                                positive_notification = True
                            elif "Annotazione" in type_ and "negativa" in type_:
                                notification = True

                        professor_name = subject_object.find_next(
                            name="i", class_="small"
                        ).get_text(strip=True)

                        mark_description = (
                            subject_object.get_text(strip=True)
                            .replace(subject, "")
                            .replace(professor_name, "")
                        )

                        if notification:
                            mark_description.replace(type_, "")

                        marks_list.append(
                            {
                                "subject": subject,
                                "mark": mark,
                                "mark_description": (
                                    mark_description.replace("-  ", "", 1)
                                    if mark_description
                                    else ""
                                ),
                                "received_for": received_for,
                                "date": date,
                                "notification": notification,
                                "positive_notification": positive_notification,
                            }
                        )

                        if marks_limit is not None:
                            marks_count += 1
                            if marks_limit == marks_count:
                                break

                    return True, marks_list
                except Exception:
                    return False, await log_with_random_path(
                        await generate_error_message(
                            error_message=traceback.format_exc(),
                            user_id=user_id,
                            current_key=current_key,
                            user_data=user_data,
                            notification=notification,
                            positive_notification=positive_notification,
                            mark_description=mark_description,
                            professor_name=professor_name,
                            type_object=type_object,
                            type_=type_,
                            subject_object=subject_object,
                            subject=subject,
                            received_for=received_for,
                            date=date,
                            center_object=center_object,
                            mark=mark,
                            marks_object=marks_object,
                            mark_object=mark_object,
                            marks_list=marks_list,
                        )
                    )
