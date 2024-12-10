import redis.asyncio as redis
from clean_settings import redis_settings

redis_client = redis.Redis(host=redis_settings.host, port=redis_settings.port)
