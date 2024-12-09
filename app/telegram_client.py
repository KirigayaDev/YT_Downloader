"""Инициализация телеграм клиента"""
from telethon import TelegramClient

from clean_settings import settings

client: TelegramClient = TelegramClient('bot.session', api_id=settings.api_id, api_hash=settings.api_hash)
