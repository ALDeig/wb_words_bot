from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_menu():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Поисковые запросы", callback_data="suggest"),
        InlineKeyboardButton(text="Сбор SEO ядра", callback_data="excel")
    )
    return kb


def subscribe():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="1 день 500р", callback_data="day"),
        InlineKeyboardButton(text="1 месяц 2900р", callback_data="month")
    )
    return kb


def paid():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Оплатил(а)", callback_data="paid")
    )
    return kb
