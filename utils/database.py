import json

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(f"sqlite:///{settings.DATABASE_FILE_NAME}.db")

Base = declarative_base()


class Wait(Base):
    __tablename__ = "wait"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(Integer)
    confirmed = Column(Boolean)
    ask_data = Column(Boolean)
    login = Column(String)
    password = Column(String)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(Integer)
    login = Column(String)
    password = Column(String)
    user_id = Column(String)
    user_data = Column(Text)
    schedule = Column(Text)
    tasks = Column(Text)
    marks = Column(Text)
    agenda = Column(Text)
    user_settings = Column(Text)
    messages = Column(Text)
    absence = Column(Text)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


async def add_user_to_wait(telegram_id: int):
    new_user = Wait(telegram_id=telegram_id, confirmed=False, ask_data=False)
    session.add(new_user)
    session.commit()


async def delete_user_from_wait(telegram_id: int):
    wait_obj = session.query(Wait).filter_by(telegram_id=telegram_id).first()
    if wait_obj:
        session.delete(wait_obj)
        session.commit()


async def user_in_wait(telegram_id: int):
    user = session.query(Wait).filter_by(telegram_id=telegram_id).first()

    return user if user else False


async def update_wait_user_by_telegram_id(telegram_id: int, confirmed: bool):
    user = session.query(Wait).filter_by(telegram_id=telegram_id).first()

    if not user:
        return False

    user.confirmed = confirmed

    session.commit()


async def update_wait_user_ask_data(telegram_id: int, ask_data: bool):
    user = session.query(Wait).filter_by(telegram_id=telegram_id).first()

    if not user:
        return False

    user.ask_data = ask_data

    session.commit()


async def set_user_wait_login(telegram_id: int, login: str):
    user = session.query(Wait).filter_by(telegram_id=telegram_id).first()

    if not user:
        return False

    user.login = login

    session.commit()


async def set_user_wait_password(telegram_id: int, password: str):
    user = session.query(Wait).filter_by(telegram_id=telegram_id).first()

    if not user:
        return False

    user.password = password

    session.commit()


async def get_all_users_wait() -> list:
    users_wait = session.query(Wait).all()
    return users_wait


async def add_user(
    telegram_id: int,
    user_id: str,
    user_data: list[dict],
    login: str,
    password: str,
    schedule: list[dict],
    tasks: list[dict],
    marks: list[dict],
    agenda: list[dict],
    user_settings: dict,
    messages: dict,
    absence: list[dict],
) -> None:
    new_user = User(
        telegram_id=telegram_id,
        user_id=user_id,
        user_data=json.dumps(user_data),
        login=login,
        password=password,
        schedule=json.dumps(schedule),
        tasks=json.dumps(tasks),
        marks=json.dumps(marks),
        agenda=json.dumps(agenda),
        user_settings=json.dumps(user_settings),
        messages=json.dumps(messages),
        absence=json.dumps(absence),
    )
    session.add(new_user)
    session.commit()


async def delete_user(telegram_id: int):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        session.delete(user)
        session.commit()


async def get_all_users() -> list:
    users = session.query(User).all()
    return users


async def update_user_by_telegram_id(telegram_id: int, **kwargs):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return False

    for key, value in kwargs.items():
        if key in [
            "schedule",
            "tasks",
            "marks",
            "agenda",
            "user_settings",
            "user_data",
            "messages",
            "absence",
        ]:
            setattr(user, key, json.dumps(value))
        else:
            setattr(user, key, value)

    session.commit()
    return True


async def find_user_by_telegram_id(telegram_id: int):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    return user if user else None


async def set_user_language(telegram_id: int, language: str):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return False

    user_settings = json.loads(user.user_settings)
    user_settings["language"] = language

    await update_user_by_telegram_id(
        telegram_id=telegram_id, user_settings=user_settings
    )
