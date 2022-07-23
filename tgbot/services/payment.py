import asyncio
from datetime import date, timedelta
from enum import Enum

from aiogram import Bot
from pyqiwip2p import AioQiwiP2P
from pyqiwip2p.AioQiwip2p import Bill
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards.inline import start_menu
from tgbot.services.db_queries import QueryDB


class BillStatus(Enum):
    WAITING = "WAITING"
    PAID = "PAID"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


RELATION_STATUS = {"REJECTED": BillStatus.REJECTED, "WAITING": BillStatus.WAITING,
                   "PAID": BillStatus.PAID, "EXPIRED": BillStatus.EXPIRED}


class Payment:
    def __init__(self, amount: int, period: int, comment: str, qiwi: AioQiwiP2P):
        self._amount = amount
        # self._user_id = user_id
        self._qiwi = qiwi
        self._comment = comment
        self.period = period
        self.bill: Bill | None = None

    async def create_bill(self) -> str:
        self.bill = await self._qiwi.bill(amount=self._amount, currency="RUB", comment=self._comment, lifetime=15)
        return self.bill.pay_url

    async def get_payment_status(self) -> BillStatus:
        bill = await self._qiwi.check(bill_id=self.bill.bill_id)
        return RELATION_STATUS[bill.status]


async def check_payment_process(user_id: int, db: AsyncSession, bot: Bot, payment: Payment):
    while True:
        await asyncio.sleep(2 * 60)
        status = await payment.get_payment_status()
        match status:
            case BillStatus.PAID:
                subscribe = date.today() + timedelta(days=payment.period)
                await QueryDB(db).add_user(user_id, subscribe)
                await bot.send_message(user_id, f"Оплата прошла успешно. Ваша подписка активна до {subscribe}")
                await bot.send_message(user_id, "https://t.me/robo_wb/573 - инструкция")
                await bot.send_message(user_id, "Выберите команду", reply_markup=start_menu())
                return
            case BillStatus.EXPIRED:
                await bot.send_message(user_id, "Истекло время оплаты. Чтобы начать заново нажмите /start")
                return
            case BillStatus.REJECTED:
                await bot.send_message(user_id, "Платеж отклонен. Чтобы начать заново нажмите /start")
                return
            case _: pass
