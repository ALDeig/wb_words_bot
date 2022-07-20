from datetime import date

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models.models import User, Authorization, Proxy
from .db_connection import get_session


class QueryDB:
    def __init__(self, session):
        self.session: AsyncSession = session

    async def get_session(self):
        self.session = await get_session()
        return self

    async def add_user(self, telegram_id: int, subscribe: date) -> User | bool:
        new_user = User(telegram_id=telegram_id, subscribe=subscribe)
        self.session.add(new_user)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return False
        return new_user

    async def get_users(self) -> list[User]:
        users = await self.session.execute(sa.select(User).order_by(User.telegram_id))
        return users.scalars().all()

    async def get_user(self, telegram_id: int) -> User | None:
        user = await self.session.execute(sa.select(User).where(User.telegram_id == telegram_id))
        return user.scalar()

    async def update_wb_api_key(self, telegram_id: int, api_key: str):
        await self.session.execute(sa.update(User).where(User.telegram_id == telegram_id).values(wb_api_key=api_key))
        await self.session.commit()

    async def delete_users_with_subscribe_over(self):
        users_without_subscribe = await self.session.execute(sa.select(User).where(User.subscribe < date.today()))
        await self.session.execute(sa.delete(User).where(User.subscribe < date.today()))
        await self.session.commit()
        return users_without_subscribe.scalars().all()

    async def delete_user(self, telegram_id):
        result = await self.session.execute(
            sa.delete(User).where(User.telegram_id == telegram_id).returning("*")
        )
        await self.session.commit()
        if result.first():
            return True
        return False

    async def get_authorization(self) -> tuple[Authorization, Proxy]:
        token = await self.session.execute(sa.select(Authorization).limit(1))
        proxy = await self.session.execute(sa.select(Proxy).limit(1))
        return token.scalar(), proxy.scalar()

    async def update_token(self, token: str):
        await self.session.execute(sa.delete(Authorization))
        new_authorization = Authorization(token=token)
        self.session.add(new_authorization)
        await self.session.commit()
        return new_authorization

    async def update_proxy(self, username: str, password: str, ip_address: str, port: int):
        await self.session.execute(sa.delete(Proxy))
        new_proxy = Proxy(username=username, password=password, ip_address=ip_address, port=port)
        self.session.add(new_proxy)
        await self.session.commit()
