"""Запуск проекта"""
import os
import shutil
import asyncio

import message_handlers
from telegram_client import client
from clean_settings import bot_settings


def main() -> None:
    """
    Функция запускающая бота
    :return:
    """
    if os.path.exists('./videos'):
        shutil.rmtree('./videos')
    client.start(bot_token=bot_settings.token)
    print('Бот запущен')
    message_handlers.print_me.log_enable_url_handlers()
    client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
