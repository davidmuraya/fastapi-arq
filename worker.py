# worker.py


from arq.connections import RedisSettings
from arq.jobs import Job
from httpx import AsyncClient

from config import get_settings
from database.connection import get_db
from schemas.models import JobHistoryCreate
from tasks import add, divide, long_call
from utils.date_parser import parse_datetime_str
from utils.job_info import process_job_info
from utils.job_info_crud import create_job_history

# Configuration settings
config = get_settings()

# Configure Redis connection
REDIS_SETTINGS = RedisSettings(host=config.redis_host, port=config.redis_port)


# ARQ startup and shutdown
async def startup(ctx):
    ctx["session"] = AsyncClient()


async def shutdown(ctx):
    await ctx["session"].aclose()


async def save_job_history_to_db(ctx: dict):
    """
    ARQ `after_job_end` hook: Saves the final status and details of a completed job
    to the database.

    This function is called by the ARQ worker after a job finishes (either
    successfully or with an error). It retrieves job information using
    `process_job_info`, prepares it for database insertion using the
    `JobHistoryCreate` schema, and then saves it via `create_job_history`.

    Args:
        ctx (dict): The ARQ job context dictionary. Expected to contain
                    'job_id' and 'redis' (ArqRedis connection).
    """
    # Extract job_id and redis connection from the ARQ context
    job_id = ctx.get("job_id")
    redis = ctx.get("redis")

    # Basic validation: job_id and redis are essential
    if not job_id or not redis:
        # Consider using logger.error here for better logging
        print(f"Error: job_id or redis not found in context for on_job_end. Job ID: {job_id}")
        return

    # Create an ARQ Job instance to interact with the job's data in Redis
    job = Job(job_id, redis)

    # Fetch comprehensive job information using the utility function.
    # process_job_info is expected to return a JobStatusResponse Pydantic model.
    job_info = await process_job_info(job)

    # If job_info couldn't be retrieved (e.g., job details not found in Redis), log and exit.
    if not job_info:
        # Consider using logger.error
        print(f"Error: Could not retrieve job_info for job_id {job_id}. Skipping DB save.")
        return

    # Prepare a dictionary with data extracted from job_info.
    # This data will be used to create a JobHistoryCreate Pydantic model.
    # Note: 'enqueue_time' is typically sourced from the initial 'ctx' if needed,
    # as job_info (JobStatusResponse) might not always carry it.
    # For this version, we are relying on fields available in job_info.
    job_history_data_dict = {
        "job_id": job_info.job_id,
        "status": job_info.status,
        "success": job_info.success,
        "result_payload": job_info.result,  # Assumes JobStatusResponse.result is a dict
        "start_time": parse_datetime_str(job_info.start_time),  # Convert string to datetime
        "finish_time": parse_datetime_str(job_info.finish_time),  # Convert string to datetime
        "username": job_info.username,
        "function_name": job_info.function,
        "args_payload": job_info.args,  # Assumes args is a string representation
        "error_message": job_info.error,
        "attempts": job_info.attempts,
    }

    # Create a Pydantic model instance for data validation and structure.
    # This helps ensure the data conforms to the expected schema before DB insertion.
    try:
        job_history_to_save = JobHistoryCreate(**job_history_data_dict)
    except Exception as e:  # Catch Pydantic validation errors or others
        # Consider using logger.error with exc_info=True for full traceback
        print(f"Error creating JobHistoryCreate model for job {job_id}: {e}")
        print(f"Data causing error: {job_history_data_dict}")
        return

    # Get a database session using the get_db generator
    db_gen = get_db()
    db = None
    try:
        db = next(db_gen)  # Get the session

        # Call the CRUD function to create the job history record in the database.
        # This function should handle adding the object to the session and committing.
        create_job_history(db=db, job_history_in=job_history_to_save)

    except Exception as e_db:
        # Consider using logger.error with exc_info=True
        print(f"Error saving job history for {job_id} to database: {e_db}")


# Worker settings for ARQ
class WorkerSettings:
    functions = [long_call, add, divide]
    on_startup = startup
    on_shutdown = shutdown
    after_job_end = save_job_history_to_db
    keep_result_forever = True
    max_jobs = 100
    max_tries = 3
    queue_name = config.WORKER_QUEUE
    redis_settings = REDIS_SETTINGS
