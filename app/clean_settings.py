from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс отвечающий за парс .env файла
    """
    bot_token: str = Field()
    api_id: str = Field()
    api_hash: str = Field()
    parallel_download_count_limit: int = Field()
    parallel_upload_count_limit: int = Field()
    max_filesize: int = Field()

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


try:
    settings = Settings()

except Exception:
    raise Exception(".env настроен неправильно")
