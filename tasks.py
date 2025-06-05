import asyncio
import logging
from typing import Optional

from httpx import AsyncClient, HTTPStatusError, RequestError


# ARQ task definitions
async def long_call(ctx, url: str, task_id: str, max_tries: int = 3):
    """
    Task to perform an HTTP GET request with retries.
    Stores progress and results in Redis.
    """
    redis = ctx["redis"]
    session: AsyncClient = ctx["session"]
    tries = ctx.get("tries", 1)

    # Update task state in Redis
    await redis.hset(
        f"task:{task_id}",
        mapping={
            "status": "PROGRESS",
            "url": url,
            "tries": str(tries),
            "max_tries": str(max_tries),
        },
    )

    try:
        response = await session.get(url, timeout=180)  # 3 minutes
        response.raise_for_status()
        result = response.json()

        # Store result in Redis
        await redis.hset(f"task:{task_id}", mapping={"status": "SUCCESS", "result": str(result)})
        return result
    except RequestError as exc:
        logging.error(f"Request error for {url}: {exc}")
        if tries >= max_tries:
            await redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": "FAILURE",
                    "error": f"Max retries exceeded: {str(exc)}",
                },
            )
            raise
        # Re-enqueue with incremented tries
        await redis.enqueue_job("long_call", url, task_id, max_tries, _tries=tries + 1)
        raise
    except HTTPStatusError as exc:
        logging.error(f"HTTP status error for {url}: {exc}")
        await redis.hset(f"task:{task_id}", mapping={"status": "FAILURE", "error": str(exc)})
        raise


async def add(ctx, x: float, y: float, username: Optional[str] = None):
    """
    Task to perform addition with simulated long-running steps.
    Stores progress and results in Redis.
    """

    print("Step 1: Starting addition")
    await asyncio.sleep(15)

    result = x + y

    # Update progress
    print("Step 2: Finished addition")
    await asyncio.sleep(15)

    # Update progress

    print("Step 3: Returning result")
    await asyncio.sleep(10)

    print(f"Result: {result}")
    return {"result": result, "username": username}


async def scheduled_add(ctx, x: float, y: float, username: Optional[str] = None):
    """
    Task to perform addition with simulated long-running steps.
    Stores progress and results in Redis.
    """

    print("Step 1: Starting addition")
    await asyncio.sleep(15)

    result = x + y

    # Update progress
    print("Step 2: Finished addition")
    await asyncio.sleep(15)

    # Update progress

    print("Step 3: Returning result")
    await asyncio.sleep(10)

    print(f"Result: {result}")
    return {"result": result, "username": username}


async def divide(ctx, x: float, y: float, username: Optional[str] = None):
    """
    Task to perform division with retries.
    Stores progress and results in Redis.
    """
    print("Step 1: Starting division")
    try:
        result = x / y

        return {"result": result, "username": username}
    except Exception as exc:
        logging.error(f"Error in divide: {exc!r}")
        # Let ARQ handle retries by raising the exception
        raise
