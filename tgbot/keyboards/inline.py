from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_menu():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Поисковые запросы", callback_data="suggest"),
        InlineKeyboardButton(text="Сбор SEO ядра", callback_data="excel"),
        InlineKeyboardButton(text="Анализ конкурента", callback_data="info"),
        # InlineKeyboardButton(text="Изменить название карточки", callback_data="change_name")
    )
    return kb


def send_api_key():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить(изменить) ключ авторизации", callback_data="wb_api_key")]
        ]
    )
    return kb


def subscribe():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="1 день 500р", callback_data="day"),
        InlineKeyboardButton(text="1 месяц 1900р", callback_data="month")
    )
    return kb


def paid():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Оплатил(а)", callback_data="paid")
    )
    return kb


def pay(payment_url: str):
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Оплатить", url=payment_url),
        # InlineKeyboardButton(text="Оплатил", callback_data="paid")
    )
    return kb
