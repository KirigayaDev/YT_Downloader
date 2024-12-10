"""Инициализация телеграм клиента"""
from telethon import TelegramClient

from clean_settings import bot_settings

client: TelegramClient = TelegramClient('./sessions/bot.session', api_id=bot_settings.api_id,
                                        api_hash=bot_settings.api_hash)
