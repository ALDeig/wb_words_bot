import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.utils.exceptions import ChatNotFound

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter, SubscribeFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.user import register_user
from tgbot.services.db_connection import get_session
from tgbot.services.logger import setup_logger
from tgbot.services.scheduler import add_new_job


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(SubscribeFilter)


def register_all_handlers(dp):
    register_user(dp)
    register_admin(dp)


async def set_commands(dp: Dispatcher):
    config = dp.bot.get('config')
    admin_ids = config.tg_bot.admin_ids
    await dp.bot.set_my_commands(
        commands=[
            BotCommand('start', 'Старт'),
            BotCommand("help", "Руководство пользователя"),
        ]
    )
    commands_for_admin = [
        BotCommand("start", "Старт"),
        BotCommand("help", "Руководство пользователя"),
        BotCommand("add_user", "Добавить пользователя бота"),
        BotCommand("authorization", "Авторизация в MPStats"),
        BotCommand("sending", "Рассылка сообщения пользователям"),
        BotCommand("count", "Количество пользователей"),
        BotCommand("delete_user", "Удалить пользователя")
    ]
    for admin_id in admin_ids:
        try:
            await dp.bot.set_my_commands(
                commands=commands_for_admin,
                scope=BotCommandScopeChat(admin_id)
            )
        except ChatNotFound as er:
            logging.error(f'Установка команд для администратора {admin_id}: {er}')


async def main():
    setup_logger("INFO")
    logging.info("Starting bot")
    config = load_config(".env")

    if config.tg_bot.use_redis:
        storage = RedisStorage()
    else:
        storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    bot['config'] = config
    bot['db'] = session = await get_session()
    bot_info = await bot.get_me()
    logging.info(f'<yellow>Name: <b>{bot_info["first_name"]}</b>, username: {bot_info["username"]}</yellow>')

    register_all_filters(dp)
    register_all_handlers(dp)
    await set_commands(dp)

    scheduler = add_new_job(session, bot)

    # start
    try:
        scheduler.start()
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
