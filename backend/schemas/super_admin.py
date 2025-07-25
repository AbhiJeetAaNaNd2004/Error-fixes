# schemas/super_admin.py

from pydantic import BaseModel, Field
from typing import Optional, List

# --- User Management Schemas ---

class AdminCreate(BaseModel):
    """Data required to create a new admin user."""
    employee_id: str = Field(..., description="The unique employee ID for the new admin.")
    employee_name: str = Field(..., description="The full name of the new admin.")
    username: str = Field(..., description="The username for the new admin to log in.")
    password: str = Field(..., min_length=8, description="The password for the new admin. Must be at least 8 characters.")
    department_id: int = Field(..., description="The ID of the department to which the admin belongs.")

class UserRoleUpdate(BaseModel):
    """Data required to change a user's role."""
    new_role_id: int = Field(..., description="The ID of the new role to assign to the user.")

class UserResponse(BaseModel):
    id: int
    employee_id: str
    employee_name: str
    username: str
    role_name: str
    department_name: str
    is_active: bool
    face_count: int # New field

    class Config:
        orm_mode = True

# --- Camera Configuration Schemas ---

class TripwireCreate(BaseModel):
    """Data required to create a new camera tripwire."""
    tripwire_name: str = Field(..., description="A descriptive name for the tripwire (e.g., 'Main_Entrance_Entry').")
    direction: str = Field(..., description="The direction of the tripwire ('vertical' or 'horizontal').")
    position: float = Field(..., gt=0, lt=1, description="The position of the tripwire as a fraction of the frame's width or height (e.g., 0.5 for the center).")
    spacing: float = Field(..., gt=0, lt=1, description="The spacing for the tripwire detection zone.")

class CameraCreate(BaseModel):
    """Data required to add a new camera."""
    camera_name: str = Field(..., description="A descriptive name for the camera (e.g., 'Lobby Camera 1').")
    camera_type: str = Field(..., description="The type or purpose of the camera (e.g., 'entry', 'exit').")
    stream_url: str = Field(..., description="The RTSP or device index URL for the camera stream.")
    resolution_w: int = Field(..., description="The width of the camera's resolution (e.g., 1920).")
    resolution_h: int = Field(..., description="The height of the camera's resolution (e.g., 1080).")
    fps: int = Field(..., description="The frames per second of the camera stream.")
    gpu_id: int = Field(..., description="The ID of the GPU to use for processing this camera's feed.")
    username: Optional[str] = Field(None, description="The username for the camera stream, if required.")
    encrypted_password: Optional[str] = Field(None, description="The password for the camera stream, if required.")
    tripwires: List[TripwireCreate] = []

class CameraUpdate(BaseModel):
    """Data for updating an existing camera's settings. All fields are optional."""
    camera_name: Optional[str] = None
    camera_type: Optional[str] = None
    stream_url: Optional[str] = None
    resolution_w: Optional[int] = None
    resolution_h: Optional[int] = None
    fps: Optional[int] = None
    gpu_id: Optional[int] = None
    username: Optional[str] = None
    encrypted_password: Optional[str] = None
    is_active: Optional[bool] = None

class TripwireUpdate(BaseModel):
    """Data for updating an existing tripwire's settings. All fields are optional."""
    tripwire_name: Optional[str] = None
    direction: Optional[str] = None
    position: Optional[float] = Field(None, gt=0, lt=1)
    spacing: Optional[float] = Field(None, gt=0, lt=1)

# --- System Settings Schema ---

class SystemSettingUpdate(BaseModel):
    """Data for updating a system setting."""
    setting_key: str
    setting_value: str
    data_type: str = Field(..., description="The data type of the setting ('float', 'integer', or 'string').")

