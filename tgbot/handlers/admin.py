import asyncio
import logging
from datetime import date, timedelta

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils.exceptions import ChatNotFound, BotBlocked

from ..services.db_queries import QueryDB


async def begin_add_user(msg: Message, state: FSMContext):
    await msg.answer("Введи id пользователя")
    await state.set_state("get_id")


async def get_id_user(msg: Message, state: FSMContext):
    try:
        tg_id = int(msg.text)
    except ValueError:
        await msg.answer("Должны быть только цифры")
        return
    await state.update_data(telegram_id=tg_id)
    await msg.answer("Введи количество дней, на которое предоставлен доступ (Отправь только цифру. Если введешь 0, \
то пользователь будет добавлен на неограниченное количество дней)")
    await state.set_state("get_count_days")


async def get_count_days(msg: Message, state: FSMContext):
    try:
        days = int(msg.text)
    except ValueError:
        await msg.answer("Неверный формат")
        return
    data = await state.get_data()
    subscribe = None if days == 0 else date.today() + timedelta(days=days)
    result = await QueryDB(msg.bot.get("db")).add_user(data["telegram_id"], subscribe)
    await state.finish()
    if not result:
        await msg.answer("Такой пользователь уже есть.")
        return
    await msg.answer("Готово")


async def begin_new_authorization_in_mpstats(msg: Message, state: FSMContext):
    await msg.answer("Введи e-mail")
    await state.set_state("get_email")


async def get_email(msg: Message, state: FSMContext):
    await state.update_data(email=msg.text)
    await msg.answer("Введи пароль")
    await state.set_state("get_password")


async def get_password(msg: Message, state: FSMContext):
    data = await state.get_data()
    await QueryDB(msg.bot.get("db")).update_authorization(data["email"], msg.text)
    await state.finish()
    await msg.answer("Готово")


async def begin_broadcaster(msg: Message, state: FSMContext):
    await msg.answer("Введи текст сообщения")
    await state.set_state("get_message")


async def sending_message(msg: Message, state: FSMContext):
    await state.finish()
    users = await QueryDB(msg.bot.get("db")).get_users()
    for user in users:
        try:
            await msg.copy_to(user.telegram_id)
            await asyncio.sleep(1)
        except (ChatNotFound, BotBlocked) as er:
            logging.error(f"Не удалось отправить сообщение. Ошибка: {er}")
    await msg.answer("Готово")


async def get_count_users(msg: Message):
    users = await QueryDB(msg.bot.get("db")).get_users()
    text = f"Количество пользователей: {len(users)}\n" + \
           "\n".join([f"{user.telegram_id} - {user.subscribe}" for user in users])
    await msg.answer(text)


async def delete_user(msg: Message, state: FSMContext):
    await msg.answer("Введи id пользователя")
    await state.set_state("get_id_for_delete")


async def get_id_for_delete(msg: Message, state: FSMContext):
    await state.finish()
    try:
        result = await QueryDB(msg.bot.get("db")).delete_user(int(msg.text))
    except ValueError:
        await msg.answer("Введите только цифры")
        return
    if not result:
        await msg.answer("Такого пользователя нет")
        return
    await msg.answer("Готово")


def register_admin(dp: Dispatcher):
    dp.register_message_handler(begin_add_user, commands=["add_user"], state="*", is_admin=True)
    dp.register_message_handler(get_id_user, state="get_id")
    dp.register_message_handler(get_count_days, state="get_count_days")
    dp.register_message_handler(begin_new_authorization_in_mpstats, commands=["authorization"], is_admin=True)
    dp.register_message_handler(get_email, state="get_email")
    dp.register_message_handler(get_password, state="get_password")
    dp.register_message_handler(begin_broadcaster, commands=["sending"], is_admin=True)
    dp.register_message_handler(sending_message, state="get_message")
    dp.register_message_handler(get_count_users, commands=["count"], is_admin=True)
    dp.register_message_handler(delete_user, commands=["delete_user"], is_admin=True)
    dp.register_message_handler(get_id_for_delete, state="get_id_for_delete")
