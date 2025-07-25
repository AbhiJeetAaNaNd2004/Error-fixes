# schemas/admin.py

from pydantic import BaseModel, Field
from typing import List, Optional

# --- Employee Creation Schema ---

class EmployeeCreate(BaseModel):
    """Data required to create a new employee user."""
    employee_id: str = Field(..., description="The unique employee ID for the new user.")
    employee_name: str = Field(..., description="The full name of the new employee.")
    username: str = Field(..., description="The username for the new employee to log in.")
    password: str = Field(..., min_length=8, description="The password for the new employee. Must be at least 8 characters.")
    department_id: int = Field(..., description="The ID of the department to which the employee belongs.")
    # The image_paths will be handled separately, as files are uploaded.

# --- Face Enrollment Schemas ---

class FaceImageResponse(BaseModel):
    id: int
    source_image: str

    class Config:
        orm_mode = True

# --- User Info Schema for Admins ---
class UserInfo(BaseModel):
    """Basic user information accessible to admins."""
    id: int
    employee_id: str
    employee_name: str

    class Config:
        orm_mode = True

