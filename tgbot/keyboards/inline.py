from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_menu():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Поисковые запросы", callback_data="suggest"),
        InlineKeyboardButton(text="Сбор SEO ядра", callback_data="excel")
    )
    return kb
