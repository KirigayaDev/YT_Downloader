"""Обработка присылаемых ссылок"""
import asyncio
import os

from telethon import events

from redis_client import redis_client

from telegram_client import client
from video_workers import VideoInfo, DownloaderUploaderHooks
from clean_settings import bot_settings


@client.on(events.NewMessage(pattern=r'^(?:(?:https?:)?\/\/)?(?:(?:(?:www|m(?:usic)?)\.)?youtu(?:\.be|be\.com)\/'
                                     r'(?:shorts\/|live\/|v\/|e(?:mbed)?\/|watch(?:\/|\?(?:\S+=\S+&)*v=)'
                                     r'|oembed\?url=https?%3A\/\/'
                                     r'(?:www|m(?:usic)?)\.youtube\.com\/watch\?(?:\S+=\S+&)*v%3D|attribution_link\?'
                                     r'(?:\S+=\S+&)*u=(?:\/|%2F)watch(?:\?|%3F)v(?:=|%3D))'
                                     r'?|www\.youtube-nocookie\.com\/embed\/)'
                                     r'([\w-]{11})[\?&#]?\S*$'))
async def handle_youtube_url(event: events.newmessage.EventCommon):
    """
    Скачивание и отправка видео по ссылке ютуба
    :param event:
    :return:
    """
    try:
        video_uid: str = event.pattern_match.group(1)
        redis_uid: str = f'youtube:video:{video_uid}'
        chat_id = event.input_chat
        input_file = await redis_client.get(redis_uid)

        progress_hook = DownloaderUploaderHooks(await client.send_message(chat_id, message='Проверяю видео'))
        if input_file is not None:
            await asyncio.gather(client.send_file(entity=chat_id, file=input_file.decode()),
                                 client.delete_messages(entity='me', message_ids=progress_hook.message_id))
            return

        progress_hook.message_id = await client.edit_message(entity=progress_hook.message_id,
                                                             message='Скачиваю видео')

        video_info = VideoInfo(url=f'https://www.youtube.com/watch?v={video_uid}', progress_hook=progress_hook)
        await video_info.download_video()
        await asyncio.gather(video_info.upload_video(), video_info.create_thumbnail(upload=True))

        input_file = await asyncio.gather(video_info.send_video(chat_id),
                                          asyncio.to_thread(video_info.remove_video_from_disc),
                                          asyncio.to_thread(video_info.remove_thumbnail_from_disc))
        input_file = input_file[0]
        await redis_client.set(redis_uid, input_file, ex=bot_settings.video_cache_ttl)

    except Exception as e:
        await client.send_message(entity=chat_id, message='Произошла ошибка при попытке отправить видео'
                                                          f' попробуйте снова {e}')
