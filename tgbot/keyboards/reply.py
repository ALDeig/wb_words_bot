from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup([
    [KeyboardButton(text="Поисковые запросы")],
    [KeyboardButton(text="Сбор поисковых слов")],
    [KeyboardButton(text="Руководство по эксплуатации")],
], resize_keyboard=True)
