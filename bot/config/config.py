from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    SLEEP_TIME: list[int] = [1700, 3500]
    START_DELAY: list[int] = [5, 100]
    AUTO_TASK: bool = True
    TASKS_TO_DO: list[str] = ["paint20pixels", "x:notpixel", "x:notcoin", "channel:notcoin", "channel:notpixel_channel", "joinSquad", "jettonTask"]
    AUTO_DRAW: bool = True
    JOIN_TG_CHANNELS: bool = True
    CLAIM_REWARD: bool = True
    AUTO_UPGRADE: bool = True
    REF_ID: str = 'f5373988314'
    IGNORED_BOOSTS: list[str] = ['paintReward']
    IN_USE_SESSIONS_PATH: str = 'bot/config/used_sessions.txt'
    NIGHT_MODE: bool = True
    NIGHT_TIME: list[int] = [1, 3]
    NIGHT_CHECKING: list[int] = [3600, 7200]
    ENERGY_LIMIT_MAX_LEVEL: int = 7
    PAINT_REWARD_MAX_LEVEL: int = 7
    RECHARGE_SPEED_MAX_LEVEL: int = 11
    POINTS_3X: bool = True

settings = Settings()
