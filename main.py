# app.py

from datetime import datetime

from arq.connections import ArqRedis, RedisSettings
from arq.jobs import Job
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session

from config import get_settings
from database.connection import get_db
from models import JobEnqueueResponse, JobStatusResponse, LongCallRequest, MathRequest
from redis_pool import get_redis_pool
from schemas.models import JobHistoryRead  # Import for type hinting if needed, though get_job_history returns it
from utils.events import on_shutdown, on_start_up
from utils.job_info import process_job_info
from utils.job_info_crud import get_job_history

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)

# FastAPI app
app = FastAPI(
    title="FastAPI with ARQ",
    version="1.0.0",
    on_startup=[on_start_up],
    on_shutdown=[on_shutdown],
)


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


@app.post("/tasks/scheduled_add", response_model=JobEnqueueResponse)
async def enqueue_scheduled_add(hour: int, min: int, request: MathRequest, redis: ArqRedis = Depends(get_redis_pool)):
    """Enqueue a job to perform addition at a scheduled time."""
    target_time = datetime.now().replace(hour=hour, minute=min, second=15, microsecond=0)

    job = await redis.enqueue_job("scheduled_add", request.x, request.y, request.username, _defer_until=target_time)
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
async def get_job_status(job_id: str, db: Session = Depends(get_db), redis: ArqRedis = Depends(get_redis_pool)) -> JobStatusResponse:
    """
    Retrieve the status and details of a background job by its job_id.
    It first checks Redis, and if not found, checks the job history database.

    Args:
        job_id (str): The unique identifier of the job.
        db (Session): Database session dependency.
        redis (ArqRedis): ARQ Redis connection dependency.

    Returns:
        JobStatusResponse: The status and metadata of the job.

    Raises:
        HTTPException: 404 if the job is not found in Redis or the database.

    Job status values from ARQ (Redis):
        - deferred: Job is in the queue, but the time it should be run has not yet been reached.
        - queued: Job is in the queue, and the time it should run has been reached.
        - in_progress: Job is currently being processed.
        - complete: Job has finished processing and the result is available.
        - not_found: Job was not found in the queue or result store.
    Job status values from Database (JobHistory):
        - Typically 'complete' or 'failed'.
    """

    # Initialize ARQ Job instance
    arq_job = Job(job_id, redis)

    # Try to get job info from ARQ/Redis
    job_info_from_redis = await process_job_info(job=arq_job)

    if job_info_from_redis:
        # If found in Redis, return that information
        print(f"Job {job_id} found in Redis")
        # process_job_info already returns JobStatusResponse
        return job_info_from_redis
    else:
        # If not found in Redis, check the database
        job_history_from_db = get_job_history(db=db, job_id=job_id)

        if job_history_from_db:
            # If found in the database, adapt JobHistoryRead to JobStatusResponse
            # Note: JobHistoryRead stores datetimes, JobStatusResponse expects ISO strings
            start_time_iso = job_history_from_db.start_time.isoformat() if job_history_from_db.start_time else None
            finish_time_iso = job_history_from_db.finish_time.isoformat() if job_history_from_db.finish_time else None

            return JobStatusResponse(
                job_id=job_history_from_db.job_id,
                status=job_history_from_db.status or "Unknown",  # Provide a default if status is None
                success=job_history_from_db.success,
                result=job_history_from_db.result_payload or {},  # Ensure result is a dict
                start_time=start_time_iso,
                finish_time=finish_time_iso,
                username=job_history_from_db.username,
                function=job_history_from_db.function_name,
                args=job_history_from_db.args_payload,
                error=job_history_from_db.error_message,
                attempts=job_history_from_db.attempts,
            )
        else:
            # If not found in Redis or the database, raise 404
            raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' was not found.")


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
