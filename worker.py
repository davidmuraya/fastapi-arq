# worker.py


from arq.connections import RedisSettings
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


async def shutdown(ctx):
    await ctx["session"].aclose()


# Worker settings for ARQ
class WorkerSettings:
    functions = [long_call, add, divide]
    on_startup = startup
    on_shutdown = shutdown
    keep_result_forever = True
    max_jobs = 100
    max_tries = 3
    queue_name = config.WORKER_QUEUE
    redis_settings = REDIS_SETTINGS
