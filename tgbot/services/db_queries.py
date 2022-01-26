from datetime import date

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models.models import User, Authorization
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
            return False
        return new_user

    async def get_users(self) -> list[User]:
        users = await self.session.execute(sa.select(User).order_by(User.telegram_id))
        return users.scalars().all()

    async def get_user(self, telegram_id: int) -> User | None:
        user = await self.session.execute(sa.select(User).where(User.telegram_id == telegram_id))
        return user.scalar()

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

    async def get_authorization(self) -> Authorization:
        auth = await self.session.execute(sa.select(Authorization).limit(1))
        return auth.scalar()

    async def update_authorization(self, email: str, password: str):
        await self.session.execute(sa.delete(Authorization))
        new_authorization = Authorization(email=email, password=password)
        self.session.add(new_authorization)
        await self.session.commit()
        return new_authorization
