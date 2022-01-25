from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .db_queries import QueryDB


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def check_subscribe_users(session):
    await QueryDB(session).delete_users_with_subscribe_over()


def add_new_job(session):
    scheduler.add_job(check_subscribe_users, "cron", hour=1, args=[session])
    return scheduler
