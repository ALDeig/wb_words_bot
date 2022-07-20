import asyncio
import hashlib
from datetime import datetime, timedelta, date
from enum import Enum

import pytz
from aiogram import Bot
from httpx import AsyncClient
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards.inline import start_menu
from tgbot.services.db_queries import QueryDB
from tgbot.services.errors import CreatePaymentError

TZ = pytz.timezone("Europe/Moscow")


class Status(Enum):
    CREATED = "NEW"
    CONFIRMED = "CONFIRMED"
    DEADLINE_EXPIRED = "DEADLINE_EXPIRED"
    CONFIRM_CHECKING = "CONFIRM_CHECKING"
    REJECTED = "REJECTED"


class CreatePaymentResponse(BaseModel):
    success: bool = Field(alias="Success")
    payment_id: int = Field(alias="PaymentId")
    error_code: int = Field(alias="ErrorCode")
    payment_url: str = Field(alias="PaymentURL")
    message: str | None = Field(alias="Message")


class PaymentStateResponse(BaseModel):
    terminal_key: str = Field(alias="TerminalKey")
    order_id: str = Field(alias="OrderId")
    status: Status = Field(alias="Status")

    def __init__(self, **kwargs):
        kwargs["Status"] = Status.CONFIRM_CHECKING \
            if kwargs["Status"] not in [status.value for status in Status] \
            else kwargs["Status"]
        super().__init__(**kwargs)


class Payment:
    def __init__(
            self, price: int, description: str, order_id: str, terminal_key: str, terminal_password: str, period: int
    ):
        self.price = price * 100
        self.description = description
        self.order_id = order_id
        self.period = period
        self._terminal_key = terminal_key
        self._terminal_password = terminal_password
        self.payment_response: CreatePaymentResponse | None = None

    async def create_payment(self) -> "CreatePaymentResponse.payment_url":
        url = "https://securepay.tinkoff.ru/v2/Init"
        async with AsyncClient() as client:
            response = await client.post(
                url=url,
                json={
                    "TerminalKey": self._terminal_key,
                    "Amount": self.price,
                    "OrderId": self.order_id,
                    "Description": self.description,
                    "RedirectDueDate": self._calculate_payment_due_datetime().isoformat(),
                    "SuccessURL": "https://t.me/SEO_WB_bot",
                    "FailURL": "https://t.me/SEO_WB_bot"
                },
                timeout=60
            )
            self.payment_response: CreatePaymentResponse = CreatePaymentResponse.parse_obj(response.json())
            if self.payment_response.error_code == 0:
                return self.payment_response.payment_url
            raise CreatePaymentError

    async def get_payment_state(self) -> PaymentStateResponse:
        url = "https://securepay.tinkoff.ru/v2/GetState"
        async with AsyncClient() as client:
            response = await client.post(
                url=url,
                json={"TerminalKey": self._terminal_key, "PaymentId": self.payment_response.payment_id,
                      "Token": self._create_token_for_check_status()},
                timeout=60
            )
            return PaymentStateResponse.parse_obj(response.json())

    def _create_token_for_check_status(self) -> str:
        params = {"Password": self._terminal_password, "PaymentId": str(self.payment_response.payment_id),
                  "TerminalKey": self._terminal_key}
        values_string = "".join(params.values())
        return hashlib.sha256(values_string.encode()).hexdigest()

    @staticmethod
    def _calculate_payment_due_datetime() -> datetime:
        expiration_date = datetime.now(tz=TZ).replace(microsecond=0) + timedelta(minutes=15)
        return expiration_date


async def check_payment_process(user_id: int, db: AsyncSession, bot: Bot, payment: Payment):
    for _ in range(5):
        payment_state = await payment.get_payment_state()
        match payment_state.status:
            case Status.CONFIRMED:
                subscribe = date.today() + timedelta(days=payment.period)
                await QueryDB(db).add_user(user_id, subscribe)
                await bot.send_message(user_id, f"Оплата прошла успешно. Ваша подписка активна до {subscribe}",
                                       reply_markup=start_menu())
                return
            case Status.DEADLINE_EXPIRED:
                await bot.send_message(user_id, "Истекло время оплаты. Чтобы начать заново нажмите /start")
                return
            case Status.REJECTED:
                await bot.send_message(user_id, "Платеж отклонен. Чтобы начать заново нажмите /start")
                return
            case _: pass
        await asyncio.sleep(60)
