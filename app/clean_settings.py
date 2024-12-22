"""
Парс и валидация конфигов
"""
from pydantic import Field
from pydantic.types import conint

from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    """
    Класс отвечающий за настройки бота
    """
    token: str = Field(alias='bot_token')
    api_id: str = Field()
    api_hash: str = Field()
    parallel_download_count_limit: conint(ge=1) = Field()
    parallel_upload_count_limit: conint(ge=1) = Field()
    max_filesize: conint(ge=1, le=2147483648) = Field()
    video_cache_ttl: conint(ge=0) = Field()
    parallel_upload_thumbnails_limit: conint(ge=1) = Field()


class RedisSettings(BaseSettings):
    host: str = Field(alias='redis_host')
    port: conint(ge=0, le=65535) = Field(alias='redis_port')


try:
    bot_settings = BotSettings()
    redis_settings = RedisSettings()

except Exception:
    raise Exception(".env настроен неправильно")
