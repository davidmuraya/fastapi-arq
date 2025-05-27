# worker.py

from typing import AsyncGenerator

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from httpx import AsyncClient

from config import get_settings
from tasks import add, divide, long_call

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)


# ARQ startup and shutdown
async def startup(ctx):
    ctx["session"] = AsyncClient()
    ctx["redis"] = await create_pool(REDIS_SETTINGS)


async def shutdown(ctx):
    await ctx["session"].aclose()
    ctx["redis"].close()


# Worker settings for ARQ
class WorkerSettings:
    functions = [long_call, add, divide]
    on_startup = startup
    on_shutdown = shutdown
    keep_result_forever = True
    max_jobs = 100
    max_tries = 3
    redis_settings = REDIS_SETTINGS


# Dependency to provide Redis pool
async def get_redis_pool() -> AsyncGenerator[ArqRedis, None]:
    redis = await create_pool(REDIS_SETTINGS)
    try:
        yield redis
    finally:
        await redis.close()
