import typing

from aiogram.dispatcher.filters import BoundFilter

from tgbot.config import Config
from tgbot.services.db_queries import QueryDB


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin: typing.Optional[bool] = None):
        self.is_admin = is_admin

    async def check(self, obj):
        if self.is_admin is None:
            return True
        config: Config = obj.bot.get('config')
        return str(obj.from_user.id) in config.tg_bot.admin_ids


class SubscribeFilter(BoundFilter):
    key = "is_subscribe"

    def __init__(self, is_subscribe: typing.Optional[bool] = None):
        self.is_subscribe = is_subscribe

    async def check(self, obj):
        if self.is_subscribe is None:
            return True
        session = obj.bot.get("db")
        user = await QueryDB(session).get_user(obj.from_user.id)
        if user:
            return True
        return False
