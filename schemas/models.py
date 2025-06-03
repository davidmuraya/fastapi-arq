from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


# Job History Schemas
class JobHistoryBase(BaseModel):
    """Base model for JobHistory, containing common fields."""

    job_id: str
    status: Optional[str] = None
    success: Optional[bool] = None
    result_payload: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    username: Optional[str] = None
    function_name: Optional[str] = None
    args_payload: Optional[str] = None
    error_message: Optional[str] = None
    attempts: Optional[int] = None


class JobHistoryCreate(JobHistoryBase):
    """Schema for creating a new JobHistory record.
    All fields from JobHistoryBase are expected during creation.
    """

    pass

    class Config:
        from_attributes = True


class JobHistoryRead(JobHistoryBase):
    """Schema for reading a JobHistory record.
    Includes all fields from the database model.
    """

    # job_id is already in JobHistoryBase and is the primary key

    class Config:
        from_attributes = True


# You can add other Pydantic models for your application below
# For example, request/response models for FastAPI endpoints if not already defined elsewhere
