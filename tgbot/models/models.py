import sqlalchemy as sa

from tgbot.services.db_connection import Base


class User(Base):
    __tablename__ = "telegram_users"
    telegram_id = sa.Column(sa.BigInteger, primary_key=True, index=True)
    subscribe = sa.Column(sa.Date(), nullable=True)


class Authorization(Base):
    __tablename__ = "authorization"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True, index=True)
    email = sa.Column(sa.String)
    password = sa.Column(sa.String)
