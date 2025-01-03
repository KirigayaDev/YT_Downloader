"""
Модуль отвечающий за работу с видео
"""
import os
import uuid
import asyncio
import subprocess
import yt_dlp

from telegram_client import client
from clean_settings import bot_settings
from redis_client import redis_client

from .progress_callbacks import DownloaderUploaderHooks

_DOWNLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_download_count_limit)
_UPLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_upload_count_limit)
_THUMBNAIL_UPLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_upload_thumbnails_limit)


def _check_video_settings(info, *args):
    if info.get('is_live') or info.get('is_upcoming') or info.get('post_live'):
        raise Exception('Нельза качать не видео')


class VideoInfo:
    """
    Класс отвечающий за работу с видео
    """

    def __init__(self, url: str, progress_hook: DownloaderUploaderHooks, cache_uid: str) -> None:
        self.url: str = url
        self.progress_hook: DownloaderUploaderHooks = progress_hook
        self.cache_uid: str = cache_uid

        self.video_id = None
        self.video_path: str = None
        self.video_size: int = 0

        self.thumbnail_id = None
        self.thumbnail_path: str = None

    async def download_video(self) -> None:
        """
        Скачивание видео с учётом ограничения одновременных скачиваний видео
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
            'retry': 32,
            'retry_sleep': 0.25,
            'match_filter': _check_video_settings,
            'no_live_from_start': True,
            'flat-playlist': True
        }
        async with _DOWNLOAD_LIMIT_MUTEX:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = await asyncio.to_thread(ydl.extract_info, url=self.url, download=True)
                self.video_path = ydl.prepare_filename(result)
                self.video_size = os.path.getsize(self.video_path)

    async def try_get_from_cache(self) -> bool:
        self.video_id = await redis_client.get(self.cache_uid)
        if self.video_id is not None:
            self.video_id = self.video_id.decode()
            return True
        return False

    async def upload_video(self) -> None:
        """
        Выгрузка видео на сервера телеграма с учётом ограничения одновременных выгрузок видео
        :return:
        """
        async with _UPLOAD_LIMIT_MUTEX:
            self.video_id = await client.upload_file(self.video_path, part_size_kb=512,
                                                     progress_callback=self.progress_hook.progress_upload_hook)

    async def create_thumbnail(self, upload: bool = False) -> None:
        self.thumbnail_path = self.video_path.rsplit('.', 1)
        self.thumbnail_path = f'{self.thumbnail_path[0]}.jpg'

        await asyncio.to_thread(subprocess.call, ['ffmpeg', '-i', self.video_path, '-ss', '00:00:00.000',
                                                  '-vframes', '1', self.thumbnail_path])
        if upload:
            await self.upload_thumbnail()

    async def upload_thumbnail(self) -> None:
        async with _THUMBNAIL_UPLOAD_LIMIT_MUTEX:
            self.thumbnail_id = await client.upload_file(self.thumbnail_path, part_size_kb=512)

    async def send_video(self, chat_id, reply_to=None, cache=False):
        try:
            info = await client.send_file(entity=chat_id, file=self.video_id, thumb=self.thumbnail_id,
                                          file_size=self.video_size, supports_streaming=True, reply_to=reply_to)
            self.video_id = info.file.id
            if cache:
                await redis_client.set(self.cache_uid, self.video_id, ex=bot_settings.video_cache_ttl)

        except Exception:
            self.video_id = None

    def remove_video_from_disc(self) -> None:
        os.remove(self.video_path)
        self.video_path = None

    def remove_thumbnail_from_disc(self) -> None:
        os.remove(self.thumbnail_path)
        self.thumbnail_path = None

    def __del__(self) -> None:
        if self.video_path is not None:
            self.remove_video_from_disc()
        if self.thumbnail_path is not None:
            self.remove_thumbnail_from_disc()
