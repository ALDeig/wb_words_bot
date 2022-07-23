import asyncio
import logging
import uuid
from pathlib import Path

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile

from tgbot.keyboards import inline
from tgbot.services.payment import Payment, check_payment_process


async def btn_subscribe(call: CallbackQuery, state: FSMContext):
    await call.answer()
    # config = call.bot.get("config")
    qiwi = call.bot.get("qiwi")
    period = "день" if call.data == "day" else "месяц"
    payment = Payment(
        amount=500 if call.data == "day" else 1900,
        comment=f"Один {period} подписки на SEO-бота",
        period=1 if call.data == "day" else 30,
        qiwi=qiwi
    )
    payment_url = await payment.create_bill()
    await call.message.answer(f"Вы выбрали 1 {period} подписки. Для перехода к окну оплаты, нажмите \"Оплатить\".",
                              reply_markup=inline.pay(payment_url))
    await check_payment_process(call.from_user.id, call.bot.get("db"), call.bot, payment)
    # payment = Payment(
    #     price=500 if call.data == "day" else 1900,
    #     description=f"Один {period} подписки на SEO-бота",
    #     order_id=f"{uuid.uuid4()}",
    #     period=1 if call.data == "day" else 30,
    #     terminal_key=config.misc.terminal_key,
    #     terminal_password=config.misc.terminal_password
    # )
    # try:
    #     payment_url = await payment.create_payment()
    # except CreatePaymentError:
    #     await call.message.answer("Не удалось создать платеж. По пробуйте позже или обратитесь к администратору.")
    #     await state.finish()
    #     return
    # await call.message.answer(f"Вы выбрали 1 {period} подписки. Для перехода к окну оплаты, нажмите \"Оплатить\"."
    #                           f"После оплаты вернитесь в бота и нажмите \"Оплатил\"",
    #                           reply_markup=inline.pay(payment_url))
    # await state.update_data(payment=payment)
    # await call.message.answer(texts.TEXTS["subscribe"], reply_markup=inline.paid())
    # await call.message.answer("После оплаты доступ автоматически откроется")
    # await check_payment_process(
    #     user_id=call.from_user.id,
    #     db=call.bot.get("db"),
    #     bot=call.bot,
    #     payment=payment
    # )
    # await state.set_state("paid")
    # await state.finish()


def register_payment(dp: Dispatcher):
    dp.register_callback_query_handler(btn_subscribe, lambda call: call.data == "day" or call.data == "month")
