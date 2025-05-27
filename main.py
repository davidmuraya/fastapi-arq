# app.py

import asyncio
from typing import Optional

from arq.connections import ArqRedis, RedisSettings
from arq.jobs import Job
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from config import get_settings
from redis_pool import get_redis_pool

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)

# FastAPI app
app = FastAPI(title="FastAPI with ARQ")


# Pydantic models for request validation
class LongCallRequest(BaseModel):
    url: HttpUrl


class MathRequest(BaseModel):
    x: float
    y: float
    username: Optional[str] = None


# FastAPI endpoints
@app.post("/tasks/long_call")
async def enqueue_long_call(request: LongCallRequest, redis: ArqRedis = Depends(get_redis_pool)):
    job = await redis.enqueue_job("long_call", request.url)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return {"job_id": job.job_id}


@app.post("/tasks/add")
async def enqueue_add(request: MathRequest, redis: ArqRedis = Depends(get_redis_pool)):
    job = await redis.enqueue_job("add", request.x, request.y, request.username)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return {"job_id": job.job_id}


@app.post("/tasks/divide")
async def enqueue_divide(request: MathRequest, redis: ArqRedis = Depends(get_redis_pool)):
    job = await redis.enqueue_job("divide", request.x, request.y, request.username)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return {"job_id": job.job_id}


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str, redis: ArqRedis = Depends(get_redis_pool)):
    try:
        # Initialize Job instance with the job_id and redis connection
        job = Job(job_id, redis)

        # Get job status
        status = await job.status()

        # Initialize response dictionary
        job_data = {"job_id": job_id, "status": status.value}

        # Get job info (optional, for additional metadata)
        job_info = await job.info()
        if job_info:
            job_data["function"] = job_info.function
            if job_info.enqueue_time is not None:
                job_data["enqueue_time"] = job_info.enqueue_time.isoformat()
            job_data["args"] = str(job_info.args)
            job_data["kwargs"] = str(job_info.kwargs)

        # Attempt to get job result if it is complete
        if status == "complete":
            try:
                result = await job.result(timeout=5)  # Timeout after 5 seconds
                job_data["result"] = result
            except asyncio.TimeoutError:
                job_data["result"] = "Result retrieval timed out"
            except Exception as e:
                job_data["result"] = f"Job failed with error: {str(e)}"

        return job_data

    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
