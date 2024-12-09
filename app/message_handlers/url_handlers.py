"""Обработка присылаемых ссылок"""
from telethon import events

from telegram_client import client
from video_workers import download_and_upload_video, DownloaderUploaderHooks


@client.on(events.NewMessage(pattern=r'^(?:(?:https?:)?\/\/)?(?:(?:(?:www|m(?:usic)?)\.)?youtu(?:\.be|be\.com)\/'
                                     r'(?:shorts\/|live\/|v\/|e(?:mbed)?\/|watch(?:\/|\?(?:\S+=\S+&)*v=)'
                                     r'|oembed\?url=https?%3A\/\/'
                                     r'(?:www|m(?:usic)?)\.youtube\.com\/watch\?(?:\S+=\S+&)*v%3D|attribution_link\?'
                                     r'(?:\S+=\S+&)*u=(?:\/|%2F)watch(?:\?|%3F)v(?:=|%3D))'
                                     r'?|www\.youtube-nocookie\.com\/embed\/)'
                                     r'([\w-]{11})[\?&#]?\S*$'))
async def handle_youtube_url(event: events.newmessage.EventCommon):
    try:
        video_uid: str = event.pattern_match.group(1)
        chat_id = event.input_chat
        progress_hook = DownloaderUploaderHooks(await client.send_message(chat_id,
                                                                          message='Проверяю видео'))

        # TODO реализовать кэширование через Redis
        progress_hook.message_id = await client.edit_message(entity=progress_hook.message_id,
                                                             message='Загружаю видео')

        file_id = await download_and_upload_video(url=f'https://www.youtube.com/watch?v={video_uid}',
                                                  progress_hook=progress_hook)
        await client.send_file(entity=chat_id, file=file_id)

    except Exception:
        await client.send_message(entity=chat_id, message='Произошла ошибка при попытке отправить видео'
                                                          ' попробуйте снова')
