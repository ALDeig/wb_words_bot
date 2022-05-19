import sqlalchemy as sa

from tgbot.services.db_connection import Base


class User(Base):
    __tablename__ = "telegram_users"
    telegram_id = sa.Column(sa.BigInteger, primary_key=True, index=True)
    subscribe = sa.Column(sa.Date(), nullable=True)
    wb_api_key = sa.Column(sa.String(), nullable=True)


class Authorization(Base):
    __tablename__ = "authorization"
    token = sa.Column(sa.String, primary_key=True)


class Proxy(Base):
    __tablename__ = "proxies"
    username = sa.Column(sa.String, primary_key=True)
    password = sa.Column(sa.String)
    ip_address = sa.Column(sa.String)
    port = sa.Column(sa.Integer)
