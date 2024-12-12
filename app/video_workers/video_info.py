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

from .progress_callbacks import DownloaderUploaderHooks

_DOWNLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_download_count_limit)
_UPLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_upload_count_limit)
_THUMBNAIL_UPLOAD_LIMIT_MUTEX = asyncio.Semaphore(bot_settings.parallel_upload_thumbnails_limit)


class VideoInfo:
    """
    Класс отвечающий за работу с видео
    """

    def __init__(self, url: str, progress_hook: DownloaderUploaderHooks):
        self.url: str = url
        self.progress_hook: DownloaderUploaderHooks = progress_hook

        self.video_id = None
        self.video_path: str = None
        self.video_size: int = 0

        self.thumbnail_id = None
        self.thumbnail_path: str = None

    async def download_video(self):
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
            'retry': 25,
            'retry-sleep': 0.1
        }
        async with _DOWNLOAD_LIMIT_MUTEX:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = await asyncio.to_thread(ydl.extract_info, url=self.url, download=True)
                self.video_path = ydl.prepare_filename(result)
                self.video_size = os.path.getsize(self.video_path)

    async def upload_video(self):
        """
        Выгрузка видео на сервера телеграма с учётом ограничения одновременных выгрузок видео
        :return:
        """
        async with _UPLOAD_LIMIT_MUTEX:
            self.video_id = await client.upload_file(self.video_path, part_size_kb=512,
                                                     progress_callback=self.progress_hook.progress_upload_hook)

    async def create_thumbnail(self, upload: bool = False):
        self.thumbnail_path = self.video_path.rsplit('.', 1)
        self.thumbnail_path = f'{self.thumbnail_path[0]}.jpg'

        await asyncio.to_thread(subprocess.call, ['ffmpeg', '-i', self.video_path, '-ss', '00:00:00.000',
                                                  '-vframes', '1', self.thumbnail_path])
        if upload:
            await self.upload_thumbnail()

    async def upload_thumbnail(self):
        async with _THUMBNAIL_UPLOAD_LIMIT_MUTEX:
            self.thumbnail_id = await client.upload_file(self.thumbnail_path, part_size_kb=512)

    async def send_video(self, chat_id, reply_to=None):
        info = await client.send_file(entity=chat_id, file=self.video_id, thumb=self.thumbnail_id,
                                      file_size=self.video_size, supports_streaming=True, reply_to=reply_to)

        self.video_id = info.file.id

    def remove_video_from_disc(self):
        os.remove(self.video_path)
        self.video_path = None

    def remove_thumbnail_from_disc(self):
        os.remove(self.thumbnail_path)
        self.thumbnail_path = None

    def __del__(self):
        if self.video_path is not None:
            self.remove_video_from_disc()
        if self.thumbnail_path is not None:
            self.remove_thumbnail_from_disc()
