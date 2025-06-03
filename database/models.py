"""Database models"""

from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

from sqlalchemy import JSON as SAJson
from sqlalchemy import Column  # For storing JSON
from sqlmodel import Field, SQLModel

from database.connection import engine


class JobHistory(SQLModel, table=True):
    """Model representing the history of ARQ jobs in the database."""

    __tablename__: ClassVar[str] = "job_history"

    job_id: str = Field(primary_key=True, index=True, description="Unique ARQ job ID")
    status: Optional[str] = Field(default=None, index=True, description="Final status of the job (e.g., complete, failed)")
    success: Optional[bool] = Field(default=None, description="Whether the job execution was successful")

    # Storing complex result as a JSON string or using SQLAlchemy's JSON type
    # For SQLModel with SQLite, JSON is often handled as TEXT. For PostgreSQL, it can be native JSON.
    # Using SAJson for broader compatibility if your backend supports it. Otherwise, use str.
    result_payload: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(SAJson), description="Result payload of the job as JSON")

    start_time: Optional[datetime] = Field(default=None, description="Timestamp when the job started processing")
    finish_time: Optional[datetime] = Field(default=None, description="Timestamp when the job finished processing")

    username: Optional[str] = Field(default=None, index=True, description="Username associated with the job, if any")
    function_name: Optional[str] = Field(default=None, index=True, description="Name of the ARQ task function executed")
    args_payload: Optional[str] = Field(default=None, description="String representation of the job's arguments")
    error_message: Optional[str] = Field(default=None, description="Error message if the job failed")
    attempts: Optional[int] = Field(default=None, description="Number of attempts made for this job")

    # You could add other fields from ctx if needed, like 'score'
    # score: Optional[int] = Field(default=None)


# -------------------------
# Configuration function
# -------------------------


def configure():
    """
    Create all tables and apply seed data.
    """
    SQLModel.metadata.create_all(bind=engine)
