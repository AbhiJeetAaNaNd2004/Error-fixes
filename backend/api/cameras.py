from fastapi import APIRouter, Depends
from typing import List

from db import db_utils
from api.auth import require_role, TokenData

router = APIRouter(
    prefix="/api",
    tags=["Cameras"]
)

# Define a Pydantic model for the camera list response for good practice
from pydantic import BaseModel

class Camera(BaseModel):
    id: int
    camera_name: str

@router.get("/cameras", response_model=List[Camera], summary="Get a list of all active cameras")
async def get_active_cameras(
    # This endpoint now requires the user to be either an 'admin' or 'super_admin'
    current_user: TokenData = Depends(require_role(["admin", "super_admin"]))
):
    """
    Fetches and returns a list of all active cameras from the database.
    Access is restricted to users with 'admin' or 'super_admin' roles.
    """
    camera_configs = db_utils.get_camera_configs()
    # We map the full config to our simpler Camera model for the response
    return [Camera(id=cam['id'], camera_name=cam['camera_name']) for cam in camera_configs]

