# redis_pool.py

from typing import AsyncGenerator

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from config import get_settings

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)


# Dependency to provide Redis pool
async def get_redis_pool() -> AsyncGenerator[ArqRedis, None]:
    try:
        redis = await create_pool(
            REDIS_SETTINGS,
            default_queue_name=config.WORKER_QUEUE,
        )
    except (RedisTimeoutError, RedisConnectionError) as exc:
        # You can log.exc_info() here if you like, or do retry logic
        raise HTTPException(status_code=503, detail="Could not connect to Redis – please try again later.") from exc

    try:
        yield redis
    finally:
        await redis.close()
