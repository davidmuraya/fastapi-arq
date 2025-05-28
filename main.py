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


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    success: Optional[bool] = False
    result: dict = {}
    start_time: Optional[str] = None
    finish_time: Optional[str] = None
    username: Optional[str] = None
    function: Optional[str] = None
    args: Optional[str] = None
    error: Optional[str] = None


class JobEnqueueResponse(BaseModel):
    job_id: str
    message: str = "Job successfully queued"
    success: Optional[bool] = True


# FastAPI endpoints
@app.post("/tasks/long_call", response_model=JobEnqueueResponse)
async def enqueue_long_call(request: LongCallRequest, redis: ArqRedis = Depends(get_redis_pool)):
    job = await redis.enqueue_job("long_call", request.url)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return JobEnqueueResponse(job_id=job.job_id)


@app.post("/tasks/add", response_model=JobEnqueueResponse)
async def enqueue_add(request: MathRequest, redis: ArqRedis = Depends(get_redis_pool)):
    job = await redis.enqueue_job("add", request.x, request.y, request.username)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return JobEnqueueResponse(job_id=job.job_id)


@app.post("/tasks/divide", response_model=JobEnqueueResponse)
async def enqueue_divide(request: MathRequest, redis: ArqRedis = Depends(get_redis_pool)):
    job = await redis.enqueue_job("divide", request.x, request.y, request.username)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return JobEnqueueResponse(job_id=job.job_id)


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, redis: ArqRedis = Depends(get_redis_pool)) -> JobStatusResponse:
    """
    Retrieve the status and details of a background job by its job_id.

    Args:
        job_id (str): The unique identifier of the job.

    Returns:
        JobStatusResponse: The status and metadata of the job.

    Job status values:
        - deferred: Job is in the queue, but the time it should be run has not yet been reached.
        - queued: Job is in the queue, and the time it should run has been reached.
        - in_progress: Job is currently being processed.
        - complete: Job has finished processing and the result is available.
        - not_found: Job was not found in the queue or result store.
    """
    # Initialize Job instance with the job_id and redis connection
    job = Job(job_id, redis)

    # Get job status
    status = await job.status()

    # Get job info and result_info
    job_info = await job.info()

    job_result_info = await job.result_info()

    print(f"{job_info=}, {job_result_info=}, {status=}")

    if job_info is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Prepare data for response model
    data = {
        "job_id": job_id,
        "status": status.value,
        "success": job_info.success,
        "result": {},
        "start_time": None,
        "finish_time": None,
        "username": None,
        "function": job_info.function,
        "args": str(job_info.args),
        "error": None,
    }

    # Extract timestamps
    if job_info.start_time:
        data["start_time"] = job_info.start_time.isoformat()
    if job_info.finish_time:
        data["finish_time"] = job_info.finish_time.isoformat()

    # Extract username from kwargs if present
    username = None
    if job_info.kwargs and isinstance(job_info.kwargs, dict):
        username = job_info.kwargs.get("username")
    data["username"] = username

    # If job is complete, fetch result or error
    if status.value == "complete":
        try:
            result = await job.result(timeout=5)
            data["result"] = result if isinstance(result, dict) else {"value": result}
        except asyncio.TimeoutError:
            data["error"] = "TimeoutError: Job took longer than 5 seconds to fetch result"
        except Exception as e:
            data["error"] = str(e)

    return JobStatusResponse(**data)


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
