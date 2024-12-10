"""
Валидация конфиг файла
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    """
    Класс отвечающий за настройки бота
    """
    token: str = Field(alias='bot_token')
    api_id: str = Field()
    api_hash: str = Field()
    parallel_download_count_limit: int = Field()
    parallel_upload_count_limit: int = Field()
    max_filesize: int = Field()
    video_cache_ttl: int = Field()


class RedisSettings(BaseSettings):
    host: str = Field(alias='redis_host')
    port: int = Field(alias='redis_port')


try:
    bot_settings = BotSettings()
    redis_settings = RedisSettings()

except Exception:
    raise Exception(".env настроен неправильно")
