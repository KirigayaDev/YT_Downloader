"""Скачивание видео и выгрузка на сервера телеграмма"""
import asyncio
import yt_dlp
import uuid
import os

from telegram_client import client
from clean_settings import bot_settings

from .progress_callbacks import DownloaderUploaderHooks

_DOWNLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_download_count_limit)
_UPLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_upload_count_limit)


async def _download_video(url: str):
    """
    Скачивание видео с учётом ограничения одновременных скачиваний видео
    :param url:
    :return:
    """
    ydl_opts = {
        'outtmpl': f'videos/%(title)s_{uuid.uuid4().hex}.%(ext)s',
        'format': 'best',
        'merge_output_format': 'mp4',
        'nooverwrites:': True,
        'restrictfilenames': True,
        'max_filesize': bot_settings.max_filesize,
        'verbose': False,
        'progress': False,
        'quiet': True,
    }
    async with _DOWNLOAD_LIMIT_MUTEX:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = await asyncio.to_thread(ydl.extract_info, url=url, download=True)
            return ydl.prepare_filename(result)


async def _upload_video(video_path: str, progress_hook: DownloaderUploaderHooks):
    """
    Выгрузка видео на сервера телеграма с учётом ограничения одновременных выгрузок видео
    :param video_path:
    :param progress_hook:
    :return:
    """
    async with _UPLOAD_LIMIT_MUTEX:
        return await client.upload_file(video_path, part_size_kb=512,
                                        progress_callback=progress_hook.progress_upload_hook)


async def download_and_upload_video(url: str, progress_hook: DownloaderUploaderHooks) -> int:
    try:
        video_path: str = await _download_video(url)
        progress_hook.message_id = await client.edit_message(entity=progress_hook.message_id,
                                                             message='Начинаю выгрузку видео на сервера телеграмма')

        file_id: str = await _upload_video(video_path, progress_hook=progress_hook)
        await asyncio.to_thread(os.remove, video_path)
        return file_id

    except Exception:
        pass

    finally:
        await client.delete_messages(entity=None, message_ids=progress_hook.message_id)
