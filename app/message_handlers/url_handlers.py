"""
Обработка присылаемых ссылок
"""
import asyncio
import re

from telethon import events

from telegram_client import client
from video_workers import VideoInfo, DownloaderUploaderHooks, DownloadLocker

_YOUTUBE_LINK_REGEX = re.compile(r'^(?:(?:https?:)?\/\/)?(?:(?:(?:www|m(?:usic)?)\.)?youtu(?:\.be|be\.com)\/'
                                 r'(?:shorts\/|live\/|v\/|e(?:mbed)?\/|watch(?:\/|\?(?:\S+=\S+&)*v=)'
                                 r'|oembed\?url=https?%3A\/\/'
                                 r'(?:www|m(?:usic)?)\.youtube\.com\/watch\?(?:\S+=\S+&)*v%3D|attribution_link\?'
                                 r'(?:\S+=\S+&)*u=(?:\/|%2F)watch(?:\?|%3F)v(?:=|%3D))'
                                 r'?|www\.youtube-nocookie\.com\/embed\/)'
                                 r'([\w-]{11})[\?&#]?\S*$')


@client.on(events.NewMessage(pattern=_YOUTUBE_LINK_REGEX,
                             incoming=True,
                             func=lambda e: e.is_private))
async def handle_youtube_url(event: events.newmessage.EventCommon):
    """
    Скачивание и отправка видео по ссылке ютуба
    :param event:
    :return:
    """
    video_uid: str = event.pattern_match.group(1)
    user_id = event.input_chat.user_id
    downloader_lock = DownloadLocker(user_id)
    video_info = VideoInfo(url=f'https://www.youtube.com/watch?v={video_uid}',
                           progress_hook=DownloaderUploaderHooks(await event.reply('Проверяю видео')),
                           cache_uid=f'youtube:video:{video_uid}')
    # Взятие видео из кэша
    if await video_info.check_cache():
        try:
            await asyncio.gather(
                client.send_file(entity=user_id, file=video_info.video_id, reply_to=event.message.id),
                client.delete_messages(entity='me', message_ids=video_info.progress_hook.message_id))
        except Exception:
            pass
        return

    # Проверка скачивается ли у юзера другое видео
    if await downloader_lock.is_locked():
        try:
            await asyncio.gather(
                event.reply("У вас уже скачивается видео\nПодождите пожалуйста пока его отправит..."),
                client.delete_messages(entity='me', message_ids=video_info.progress_hook.message_id))
        except Exception:
            pass
        return

    # Процесс скачивания видео
    try:
        video_info.progress_hook.message_id = await client.edit_message(entity=video_info.progress_hook.message_id,
                                                                        message='Скачиваю видео')
        async with downloader_lock:
            await video_info.download_video()
            await asyncio.gather(video_info.upload_video(), video_info.create_thumbnail(upload=True))

            # Отправка видео и очистка его с диска
            await asyncio.gather(video_info.send_video(user_id, reply_to=event.message.id, cache=True),
                                 client.delete_messages(entity='me', message_ids=video_info.progress_hook.message_id),
                                 asyncio.to_thread(video_info.remove_video_from_disc),
                                 asyncio.to_thread(video_info.remove_thumbnail_from_disc))

    except Exception:
        await event.reply('Произошла ошибка при попытке отправить видео\nПопробуйте снова')
