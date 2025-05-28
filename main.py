# app.py

import asyncio

from arq.connections import ArqRedis, RedisSettings
from arq.jobs import Job
from fastapi import Depends, FastAPI, HTTPException

from config import get_settings
from models import JobEnqueueResponse, JobStatusResponse, LongCallRequest, MathRequest
from redis_pool import get_redis_pool

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)

# FastAPI app
app = FastAPI(title="FastAPI with ARQ")


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

    start_time = None

    # Get job info and result_info
    job_info = await job.info()

    if job_info is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get job status
    status = await job.status()

    # Set enqueue_time as start_time if available
    start_time = getattr(job_info, "enqueue_time", None)

    # Prepare data for response model
    data = {
        "job_id": job_id,
        "status": status.value,
        "success": getattr(job_info, "success", False),  # Fix: default to False if not present
        "result": {},
        "start_time": None,
        "finish_time": None,
        "username": None,
        "function": getattr(job_info, "function", None),
        "args": str(getattr(job_info, "args", "")),
        "error": None,
        "attempts": getattr(job_info, "job_try", 0),
    }

    # Extract timestamps
    if status.value == "in_progress":
        # Use enqueue_time as start_time if available
        data["start_time"] = start_time.isoformat() if start_time else None

    else:
        start_time = getattr(job_info, "start_time", None)
        data["start_time"] = start_time.isoformat() if start_time else None

    finish_time = getattr(job_info, "finish_time", None)
    data["finish_time"] = finish_time.isoformat() if finish_time else None

    # if a start_time is present, and the status is not_found, set status to queued
    # this is to handle a rare case where the job has been queued but arq is not running
    if start_time and status.value == "not_found":
        data["status"] = "queued"

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
