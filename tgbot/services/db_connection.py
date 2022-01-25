import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from tgbot.config import load_config
# from tgbot.services.db_base import Base

config = load_config()
DATABASE_URL = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}"


engine = create_async_engine(DATABASE_URL, future=True)
Base = declarative_base()
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        return session


#



# asyncio.run(test())
# async def create_db_session(config: Config):
#     engine = create_async_engine(database_url, future=True)
#     async_session = sessionmaker(
#         engine, expire_on_commit=False, class_=AsyncSession
#     )
#     logging.info("Connect to database is successfully")
#     return async_session
