from typing import List, Optional

from sqlmodel import Session, select

from database.models import JobHistory  # This is your SQLModel table class
from schemas.models import JobHistoryCreate, JobHistoryRead  # These are your Pydantic schemas


def create_job_history(db: Session, job_history_in: JobHistoryCreate) -> JobHistoryRead:
    """
    Create a new job history record in the database.
    """
    # Convert Pydantic model (JobHistoryCreate) to SQLModel table object (JobHistory)
    db_job_history = JobHistory.model_validate(job_history_in)
    db.add(db_job_history)
    db.commit()
    db.refresh(db_job_history)
    # Return as JobHistoryRead schema
    return JobHistoryRead.model_validate(db_job_history)


def get_job_history(db: Session, job_id: str) -> Optional[JobHistoryRead]:
    """
    Retrieve a specific job history record by its job_id.
    """
    statement = select(JobHistory).where(JobHistory.job_id == job_id)
    db_job_history = db.exec(statement).first()
    if db_job_history:
        return JobHistoryRead.model_validate(db_job_history)
    return None


def get_all_job_histories(db: Session, skip: int = 0, limit: int = 100) -> List[JobHistoryRead]:
    """
    Retrieve all job history records with pagination.
    """
    statement = select(JobHistory).offset(skip).limit(limit)
    db_job_histories = db.exec(statement).all()
    return [JobHistoryRead.model_validate(jh) for jh in db_job_histories]


def update_job_history(db: Session, job_id: str, job_history_update_in: JobHistoryCreate) -> Optional[JobHistoryRead]:
    """
    Update an existing job history record.
    This performs a full update based on JobHistoryCreate.
    For partial updates, you might want a different schema (e.g., JobHistoryUpdate).
    """
    statement = select(JobHistory).where(JobHistory.job_id == job_id)
    db_job_history = db.exec(statement).first()

    if not db_job_history:
        return None

    # Get data from the input Pydantic model
    update_data = job_history_update_in.model_dump(exclude_unset=True)

    # Update the SQLModel instance
    for key, value in update_data.items():
        setattr(db_job_history, key, value)

    db.add(db_job_history)
    db.commit()
    db.refresh(db_job_history)
    return JobHistoryRead.model_validate(db_job_history)


def delete_job_history(db: Session, job_id: str) -> Optional[JobHistoryRead]:
    """
    Delete a job history record by its job_id.
    Returns the deleted record or None if not found.
    """
    statement = select(JobHistory).where(JobHistory.job_id == job_id)
    db_job_history = db.exec(statement).first()

    if not db_job_history:
        return None

    # To return the object after deletion, we model_validate it first
    deleted_job_history_read = JobHistoryRead.model_validate(db_job_history)

    db.delete(db_job_history)
    db.commit()

    return deleted_job_history_read


# Example usage (you would typically call these from your API endpoints or worker):
# from database.connection import get_session # Assuming you have a get_session dependency
#
# def example_crud_operations():
#     with get_session() as session:
#         # Create
#         new_job_data = JobHistoryCreate(
#             job_id="test_job_123",
#             status="complete",
#             success=True,
#             function_name="example_task",
#             # ... other fields
#         )
#         created_job = create_job_history(db=session, job_history_in=new_job_data)
#         print(f"Created job: {created_job.job_id}")
#
#         # Read one
#         retrieved_job = get_job_history(db=session, job_id="test_job_123")
#         if retrieved_job:
#             print(f"Retrieved job: {retrieved_job.job_id}, Status: {retrieved_job.status}")
#
#         # Read all
#         all_jobs = get_all_job_histories(db=session, limit=10)
#         print(f"Found {len(all_jobs)} jobs.")
#         for job in all_jobs:
#             print(f" - Job ID: {job.job_id}")
#
#         # Update
#         update_data = JobHistoryCreate(
#             job_id="test_job_123", # job_id is used for lookup, not updated itself here
#             status="completed_with_notes",
#             success=True,
#             function_name="example_task_updated",
#             error_message="No errors, just notes."
#             # ... other fields
#         )
#         updated_job = update_job_history(db=session, job_id="test_job_123", job_history_update_in=update_data)
#         if updated_job:
#             print(f"Updated job: {updated_job.job_id}, New Status: {updated_job.status}")
#
#         # Delete
#         # deleted_job = delete_job_history(db=session, job_id="test_job_123")
#         # if deleted_job:
#         #     print(f"Deleted job: {deleted_job.job_id}")
