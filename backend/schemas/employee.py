# schemas/employee.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AttendanceRecord(BaseModel):
    """
    Pydantic model for representing a single attendance record for an employee.
    """
    id: int
    event_type: str = Field(..., description="The type of event (e.g., 'check_in', 'check_out').")
    event_timestamp: datetime = Field(..., description="The exact timestamp of the event.")
    camera_name: Optional[str] = Field(None, description="The name of the camera that recorded the event.")
    source: str = Field(..., description="The source of the event log (e.g., 'face_recognition').")

    class Config:
        orm_mode = True

