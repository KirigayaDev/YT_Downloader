"""
Коллбэки для отображения прогрессов видео
"""
import math
from telegram_client import client


class DownloaderUploaderHooks:
    def __init__(self, message_id: str):
        self.message_id = message_id

    async def progress_upload_hook(self, sent: int, total: int):
        """
        Отображение прогресса выгрузки видео на сервера телеграма
        :param sent:
        :param total:
        :return:
        """
        progress_percent = round(sent / total * 100)
        progress_len = math.floor(round(sent / total * 10))
        try:
            self.message_id = await client.edit_message(entity=self.message_id,
                                                        message=f'{"■" * progress_len}{"□" * (10 - progress_len)}'
                                                                f' {progress_percent}%')

        except Exception:
            pass
