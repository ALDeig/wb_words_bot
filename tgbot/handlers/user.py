import asyncio
import logging
import uuid
from pathlib import Path

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile

from ..keyboards import inline
from ..services import wildberries, mpstats, excel, texts
from ..services.db_queries import QueryDB
from ..services.errors import WBAuthorizedError, WBUpdateNameError, CreatePaymentError
from ..services.payment import Payment, check_payment_process


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
    config = call.bot.get("config")
    period = "день" if call.data == "day" else "месяц"
    payment = Payment(
        price=500 if call.data == "day" else 1900,
        description=f"Один {period} подписки на SEO-бота",
        order_id=f"{uuid.uuid4()}",
        period=1 if call.data == "day" else 30,
        terminal_key=config.misc.terminal_key,
        terminal_password=config.misc.terminal_password
    )
    try:
        payment_url = await payment.create_payment()
    except CreatePaymentError:
        await call.message.answer("Не удалось создать платеж. По пробуйте позже или обратитесь к администратору.")
        await state.finish()
        return
    await call.message.answer(f"Вы выбрали 1 {period} подписки. Для перехода к окну оплаты, нажмите \"Оплатить\"."
                              f"После оплаты вернитесь в бота и нажмите \"Оплатил\"",
                              reply_markup=inline.pay(payment_url))
    await state.update_data(payment=payment)
    # await call.message.answer(texts.TEXTS["subscribe"], reply_markup=inline.paid(payment_url))
    # await call.message.answer("После оплаты доступ автоматически откроется")
    # await check_payment_process(
    #     user_id=call.from_user.id,
    #     db=call.bot.get("db"),
    #     bot=call.bot,
    #     payment=payment
    # )
    await state.set_state("paid")
    # await state.finish()


async def btn_paid(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    payment = data.get("payment")
    await call.message.edit_text("Оплата проверяется")
    # await call.message.edit_reply_markup()
    await check_payment_process(call.from_user.id, call.bot.get("db"), call.bot, payment)
    await state.finish()
    # await call.message.edit_reply_markup()
    # await call.message.answer(texts.TEXTS["paid"])


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
    auth, proxy = await QueryDB(msg.bot.get("db")).get_authorization()
    query_info = mpstats.InfoByQuery(msg.text, auth.token, proxy)
    await query_info.start_process()
    # data_for_excel = mpstats.get_keywords_by_search_query(msg.text, auth.token, proxy)
    # if not data_for_excel:
    #     await msg.answer(texts.TEXTS["error"])
    #     await state.finish()
    #     return
    # excel.save_file_with_words_by_search_query(f"{msg.from_user.id}.xlsx", data_for_excel)
    excel.save_file_with_words_by_scu(f"{msg.from_user.id}.xlsx", query_info.result)
    file = InputFile(f"{msg.from_user.id}.xlsx")
    await msg.answer_document(file, caption=f"Всего слов - {len(query_info.result)}")
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
    except ValueError:
        await msg.answer("Артикул должен быть числом")
        return
    await state.finish()
    auth, proxy = await QueryDB(msg.bot.get("db")).get_authorization()
    try:
        scu_info = mpstats.InfoByScu(scu, auth.token)
        await scu_info.get_info_by_scu()
    except Exception as er:
        print(er)
        await msg.answer(texts.TEXTS["error"])
        return
    excel.save_file_with_words_by_scu(f"{scu}_words.xlsx", scu_info.words)
    excel.save_file_with_sales_by_scu(f"{scu}_sales.xlsx", scu_info.sales)
    excel.save_file_with_request(f"{scu}_requests.xlsx", scu_info.requests)
    file_words = InputFile(f"{scu}_words.xlsx")
    file_requests = InputFile(f"{scu}_requests.xlsx")
    file_sales = InputFile(f"{scu}_sales.xlsx")
    image = InputFile(scu_info.image)
    # categories = Path(f"{scu}_categories.txt")
    # categories.write_text(f"Категории:\n{scu_info.categories}")
    # file_categories = InputFile(categories)
    caption = f"<b>{scu_info.scu_info.name}</b>\n\n<u>Суммарно за 60 дней продано:</u>\n" \
              f"{scu_info.scu_info.amount_sales} шт. на {scu_info.scu_info.total_sales} руб.\n" \
              f"Цена: {scu_info.scu_info.price}"
    await msg.answer_photo(image, caption=caption)
    await msg.answer(f"Категории:\n\n{scu_info.categories}")
    # await msg.answer_document(file_categories)
    await msg.answer_document(file_words, caption=f"Всего слов - {len(scu_info.words)}")
    await msg.answer_document(file_requests, caption=f"Всего запросов - {len(scu_info.requests)}")
    await msg.answer_document(file_sales)
    await asyncio.sleep(5)
    Path(f"{scu}_words.xlsx").unlink()
    Path(f"{scu}_requests.xlsx").unlink()
    Path(f"{scu}_sales.xlsx").unlink()
    # categories.unlink()
    scu_info.image.unlink()
    await msg.answer("Выбери команду", reply_markup=inline.start_menu())


async def btn_change_name(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await QueryDB(call.bot.get("db")).get_user(call.from_user.id)
    if not user.wb_api_key:
        kb = inline.send_api_key()
        await call.message.answer("Вам нужно ввести новый ключ API Wildberries", reply_markup=kb)
        return
    await state.update_data(api_key=user.wb_api_key)
    await call.message.answer("Напишите артикул карточки")
    await state.set_state("get_scu_for_change_name")


async def get_scu_for_change_name(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("Артикул должен быть числом")
        return
    await state.update_data(scu=msg.text)
    await msg.answer("Введите новое название")
    await state.set_state("get_new_name")


async def get_new_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    try:
        await wildberries.update_name_wb_card(data["api_key"], int(data["scu"]), msg.text)
    except WBAuthorizedError as er:
        await msg.answer(f"Ошибка авторизации - {er.message}. Попробуйте изменить ключ API Wildberries",
                         reply_markup=inline.send_api_key())
    except WBUpdateNameError as er:
        await msg.answer(f"При изменении имени в карточке возникла ошибка - {er.message}. "
                         f"Исправьте данные в карточке и повторите")
    else:
        await msg.answer("Готово")
    finally:
        await state.finish()


async def btn_send_api_key(call: CallbackQuery, state: FSMContext):
    config = call.bot.get("config")
    video_id = config.misc.get_token_video_id
    # video = await call.message.answer_video(InputFile("get_token.mp4"))
    # print(video)
    await call.message.answer_video(video_id)
    await call.message.answer(texts.TEXTS["get_token"])
    await state.set_state("get_api_key")


async def get_wb_api_key(msg: Message, state: FSMContext):
    await QueryDB(msg.bot.get("db")).update_wb_api_key(msg.from_user.id, msg.text)
    await msg.answer("Готово!\nВыберите команду", reply_markup=inline.start_menu())
    await state.finish()


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(btn_subscribe, lambda call: call.data == "day" or call.data == "month")
    dp.register_callback_query_handler(btn_paid, lambda call: call.data == "paid", state="paid")
    dp.register_callback_query_handler(btn_get_suggest, lambda call: call.data == "suggest", is_subscribe=True)
    dp.register_message_handler(send_suggest_query, state="query_for_suggest")
    dp.register_callback_query_handler(btn_excel_file, lambda call: call.data == "excel", is_subscribe=True)
    dp.register_message_handler(send_excel_file, state="query_for_excel")
    dp.register_message_handler(send_help, commands=["help"])
    dp.register_callback_query_handler(btn_info_by_scu, lambda call: call.data == "info", is_subscribe=True)
    dp.register_message_handler(get_scu, state="get_scu")
    dp.register_callback_query_handler(btn_change_name, text="change_name")
    dp.register_message_handler(get_scu_for_change_name, state="get_scu_for_change_name")
    dp.register_message_handler(get_new_name, state="get_new_name")
    dp.register_callback_query_handler(btn_send_api_key, text="wb_api_key")
    dp.register_message_handler(get_wb_api_key, state="get_api_key")
