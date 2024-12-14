"""
Обработка присылаемых ссылок
"""
import asyncio
import re

from telethon import events

from redis_client import redis_client

from telegram_client import client
from video_workers import VideoInfo, DownloaderUploaderHooks
from clean_settings import bot_settings

_YOUTUBE_LINK_REGEX = re.compile(r'^(?:(?:https?:)?\/\/)?(?:(?:(?:www|m(?:usic)?)\.)?youtu(?:\.be|be\.com)\/'
                                 r'(?:shorts\/|live\/|v\/|e(?:mbed)?\/|watch(?:\/|\?(?:\S+=\S+&)*v=)'
                                 r'|oembed\?url=https?%3A\/\/'
                                 r'(?:www|m(?:usic)?)\.youtube\.com\/watch\?(?:\S+=\S+&)*v%3D|attribution_link\?'
                                 r'(?:\S+=\S+&)*u=(?:\/|%2F)watch(?:\?|%3F)v(?:=|%3D))'
                                 r'?|www\.youtube-nocookie\.com\/embed\/)'
                                 r'([\w-]{11})[\?&#]?\S*$')


@client.on(events.NewMessage(pattern=_YOUTUBE_LINK_REGEX,
                             incoming=True))
async def handle_youtube_url(event: events.newmessage.EventCommon):
    """
    Скачивание и отправка видео по ссылке ютуба
    :param event:
    :return:
    """
    try:
        video_uid: str = event.pattern_match.group(1)
        redis_uid: str = f'youtube:video:{video_uid}'
        chat = event.input_chat
        downloader_uid = f'downloader:{chat}'
        video_info = VideoInfo(url=f'https://www.youtube.com/watch?v={video_uid}',
                               progress_hook=DownloaderUploaderHooks(await event.reply('Проверяю видео')))
        video_info.video_id = await redis_client.get(redis_uid)

        if video_info.video_id is not None:
            await asyncio.gather(
                client.send_file(entity=chat, file=video_info.video_id.decode(), reply_to=event.message.id),
                client.delete_messages(entity='me', message_ids=video_info.progress_hook.message_id))
            return

        if await redis_client.get(downloader_uid):
            await asyncio.gather(
                event.reply("У вас уже скачивается видео\nПодождите пожалуйста пока его отправит..."),
                client.delete_messages(entity='me', message_ids=video_info.progress_hook.message_id))
            return

        video_info.progress_hook.message_id = await client.edit_message(entity=video_info.progress_hook.message_id,
                                                                        message='Скачиваю видео')

        await asyncio.gather(redis_client.set(downloader_uid, 1, ex=600), video_info.download_video())
        await asyncio.gather(video_info.upload_video(), video_info.create_thumbnail(upload=True))

        await asyncio.gather(video_info.send_video(chat, reply_to=event.message.id),
                             client.delete_messages(entity='me', message_ids=video_info.progress_hook.message_id),
                             asyncio.to_thread(video_info.remove_video_from_disc),
                             asyncio.to_thread(video_info.remove_thumbnail_from_disc))

        if video_info.video_id is not None:
            await redis_client.set(redis_uid, video_info.video_id, ex=bot_settings.video_cache_ttl)

    except Exception as e:
        await event.reply(f'Произошла ошибка при попытке отправить видео\nПопробуйте снова')

    finally:
        await redis_client.delete(downloader_uid)
