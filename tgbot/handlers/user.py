import asyncio
import logging
from pathlib import Path

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile

# from tgbot.models.users import User
from ..keyboards import inline, reply
from ..services import wildberries, mpstats, excel, texts
from ..services.db_queries import QueryDB


async def user_start(msg: Message, state: FSMContext):
    await state.finish()
    user = await QueryDB(msg.bot.get("db")).get_user(msg.from_user.id)
    if not user:
        await msg.answer(texts.TEXTS["start"])
        await msg.answer("Оформить подписку", reply_markup=inline.subscribe())
        return
    await msg.answer("Выбери команду", reply_markup=inline.start_menu())


async def btn_subscribe(call: CallbackQuery, state: FSMContext):
    await call.answer()
    period = "день" if call.data == "day" else "месяц"
    await call.message.answer(f"Вы выбрали 1 {period} подписки")
    await call.message.answer(texts.TEXTS["subscribe"], reply_markup=inline.paid())


async def paid(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup()
    await call.message.answer(texts.TEXTS["paid"])


async def btn_get_suggest(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup()
    await call.message.answer(texts.TEXTS["command_1"])
    await state.set_state("query_for_suggest")


async def send_suggest_query(msg: Message, state: FSMContext):
    await state.finish()
    if msg.text.isdigit():
        await msg.answer("Запрос не может быть числом")
        return
    await msg.answer("Это займет некоторое время...")
    suggest_queries = await wildberries.get_suggest_queries(msg.text)
    if not suggest_queries:
        await msg.answer(texts.TEXTS["error"])
        return
    await msg.answer("\n".join(suggest_queries))
    await msg.answer("Выбери команду", reply_markup=inline.start_menu())


async def btn_excel_file(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup()
    await call.message.answer(texts.TEXTS["command_2"])
    await state.set_state("query_for_excel")


async def send_excel_file(msg: Message, state: FSMContext):
    await state.finish()
    await msg.answer("Это займет некоторое время...")
    auth = await QueryDB(msg.bot.get("db")).get_authorization()
    data_for_excel = await mpstats.get_keywords_by_search_query(msg.text, auth.email, auth.password)
    if not data_for_excel:
        await msg.answer(texts.TEXTS["error"])
        await state.finish()
        return
    excel.save_file_with_words_by_search_query(f"{msg.from_user.id}.xlsx", data_for_excel)
    file = InputFile(f"{msg.from_user.id}.xlsx")
    await msg.answer_document(file)
    await asyncio.sleep(10)
    Path(f"{msg.from_user.id}.xlsx").unlink()
    await msg.answer("Выбери команду", reply_markup=inline.start_menu())


async def send_help(msg: Message, state: FSMContext):
    await state.finish()
    await msg.answer(texts.TEXTS["help"])
    file = InputFile("help.mp4")
    await msg.answer_document(file)


async def btn_info_by_scu(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await call.message.edit_text("Введи артикул товара")
    except Exception as er:
        logging.error(er)
        await call.message.answer("Введи артикул товара")
    await state.set_state("get_scu")


async def get_scu(msg: Message, state: FSMContext):
    try:
        scu = int(msg.text)
    except TypeError:
        await msg.answer("Артикул должен быть числом")
        return
    await state.finish()
    auth = await QueryDB(msg.bot.get("db")).get_authorization()
    try:
        categories, words, sales = await mpstats.get_info_by_scu(scu, auth.email, auth.password)
    except TypeError:
        await msg.answer(texts.TEXTS["error"])
        return
    excel.save_file_with_words_by_scu(f"{scu}_words.xlsx", words)
    excel.save_file_with_sales_by_scu(f"{scu}_sales.xlsx", sales)
    file_words = InputFile(f"{scu}_words.xlsx")
    file_sales = InputFile(f"{scu}_sales.xlsx")
    await msg.answer(f"Категории:\n{categories}")
    await msg.answer_document(file_words)
    await msg.answer_document(file_sales)
    await asyncio.sleep(5)
    Path(f"{scu}_words.xlsx").unlink()
    Path(f"{scu}_sales.xlsx").unlink()
    await msg.answer("Выбери команду", reply_markup=inline.start_menu())


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(btn_subscribe, lambda call: call.data == "day" or call.data == "month")
    dp.register_callback_query_handler(paid, lambda call: call.data == "paid")
    dp.register_callback_query_handler(btn_get_suggest, lambda call: call.data == "suggest", is_subscribe=True)
    dp.register_message_handler(send_suggest_query, state="query_for_suggest")
    dp.register_callback_query_handler(btn_excel_file, lambda call: call.data == "excel", is_subscribe=True)
    dp.register_message_handler(send_excel_file, state="query_for_excel")
    dp.register_message_handler(send_help, commands=["help"])
    dp.register_callback_query_handler(btn_info_by_scu, lambda call: call.data == "info", is_subscribe=True)
    dp.register_message_handler(get_scu, state="get_scu")
