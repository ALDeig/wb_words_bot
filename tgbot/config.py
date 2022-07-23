from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: int
    use_redis: bool


@dataclass
class Miscellaneous:
    qiwi_token: str = None
    # other_params: str = None
    # token: str = None
    help_video_id: str = None
    # terminal_key: str = None
    # terminal_password: str = None
    get_token_video_id: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=env.list("ADMINS"),
            use_redis=env.bool("USE_REDIS"),
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            get_token_video_id=env.str("GET_TOKEN_VIDEO_ID"),
            help_video_id=env.str("HELP_VIDEO_ID"),
            qiwi_token=env.str("QIWI_TOKEN")
            # terminal_key=env.str("TERMINAL_KEY"),
            # terminal_password=env.str("TERMINAL_PASSWORD")
            # wb_api_salt=env.str("WB_API_SALT")
        )
    )
