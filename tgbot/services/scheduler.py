from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from .db_queries import QueryDB


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def check_subscribe_users(session: AsyncSession, bot: Bot):
    users = await QueryDB(session).delete_users_with_subscribe_over()
    for user in users:
        await bot.send_message(user.telegram_id, "У вас закончилась подписка для продления  нажмите команду старт ")


def add_new_job(session, bot):
    scheduler.add_job(check_subscribe_users, "cron", hour=1, minute=0, args=[session, bot])
    return scheduler
