import asyncio

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
        try:
            self.message_id = await client.edit_message(entity=self.message_id, message=f'{round(sent / total * 100)}%')

        except Exception:
            pass
