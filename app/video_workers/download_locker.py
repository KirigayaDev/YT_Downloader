from redis_client import redis_client


class DownloadLocker:
    def __init__(self, downloader_uid: str):
        self.downloader_uid: str = downloader_uid

    async def __aenter__(self):
        await redis_client.set(self.downloader_uid, 1, ex=60)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await redis_client.delete(self.downloader_uid)
