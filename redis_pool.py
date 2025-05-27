# redis_pool.py

from typing import AsyncGenerator

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from config import get_settings

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)


# Dependency to provide Redis pool
async def get_redis_pool() -> AsyncGenerator[ArqRedis, None]:
    redis = await create_pool(REDIS_SETTINGS, default_queue_name=config.WORKER_QUEUE)
    try:
        yield redis
    finally:
        await redis.close()
