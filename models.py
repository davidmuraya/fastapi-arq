# models.py

from typing import Optional

from pydantic import BaseModel, HttpUrl


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
    attempts: Optional[int] = 0


class JobEnqueueResponse(BaseModel):
    job_id: str
    message: str = "Job successfully queued."
    success: Optional[bool] = True
