from telethon import events

from telegram_client import client
from .url_handlers import _YOUTUBE_LINK_REGEX


@client.on(events.NewMessage(func=lambda e: not _YOUTUBE_LINK_REGEX.match(e.message.text), incoming=True))
async def send_guide(event: events.newmessage.EventCommon):
    await event.reply("Привет, я бот для скачивания видео с ютуба\n"
                      "Отправь мне ссылку на загрузку видео с ютуба и я пришлю тебе видео")
