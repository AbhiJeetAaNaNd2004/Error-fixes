# api/super_admin.py

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from db import db_utils
from api.auth import require_role
from schemas.super_admin import (
    AdminCreate, UserRoleUpdate, UserResponse,
    CameraCreate, CameraUpdate, TripwireCreate, TripwireUpdate,
    SystemSettingUpdate
)
from dependencies import app_state
from core.tracker import FaceTrackingSystem


router = APIRouter(
    prefix="/superadmin",
    tags=["Super Admin"],
    dependencies=[Depends(require_role(["super_admin"]))]
)

def get_tracker() -> FaceTrackingSystem:
    """Dependency to get the tracker instance from the shared app state."""
    tracker = app_state.get("tracker")
    if not tracker:
        raise HTTPException(status_code=503, detail="Tracker service not available.")
    return tracker

# --- Global Tracker Control Endpoints ---

@router.post("/tracker/start", summary="Start the Face Tracking Service (All Cameras)")
def start_tracker_service(tracker: FaceTrackingSystem = Depends(get_tracker)):
    """
    Starts the face recognition and tracking service for all cameras.
    Returns an error if the service is already running.
    """
    if not tracker.start_tracking():
        raise HTTPException(status_code=409, detail="Tracker service is already running.")
    return {"message": "Face tracking service started successfully for all cameras."}

@router.post("/tracker/stop", summary="Stop the Face Tracking Service (All Cameras)")
def stop_tracker_service(tracker: FaceTrackingSystem = Depends(get_tracker)):
    """
    Stops the face recognition and tracking service for all cameras.
    Returns an error if the service is not running.
    """
    if not tracker.stop_tracking():
        raise HTTPException(status_code=409, detail="Tracker service is not currently running.")
    return {"message": "Face tracking service stopped successfully for all cameras."}

@router.get("/tracker/status", summary="Get the Status of the Tracking Service and All Cameras")
def get_tracker_status(tracker: FaceTrackingSystem = Depends(get_tracker)):
    """
    Returns the current operational status of the tracking service and each camera.
    """
    return tracker.get_status()

# --- Per-Camera Control Endpoints ---

@router.post("/cameras/{camera_id}/start", summary="Start a Single Camera's Feed")
def start_single_camera(camera_id: int, tracker: FaceTrackingSystem = Depends(get_tracker)):
    """Starts the processing thread for a specific camera."""
    if not tracker.start_camera(camera_id):
        raise HTTPException(status_code=409, detail=f"Camera {camera_id} is already running or does not exist.")
    return {"message": f"Successfully started camera {camera_id}."}

@router.post("/cameras/{camera_id}/stop", summary="Stop a Single Camera's Feed")
def stop_single_camera(camera_id: int, tracker: FaceTrackingSystem = Depends(get_tracker)):
    """Stops the processing thread for a specific camera."""
    if not tracker.stop_camera(camera_id):
        raise HTTPException(status_code=409, detail=f"Camera {camera_id} is not running or does not exist.")
    return {"message": f"Successfully stopped camera {camera_id}."}


# --- User Management Endpoints ---

@router.post("/users/create/admin", status_code=status.HTTP_201_CREATED, summary="Create a new Admin User")
def create_admin_user(admin_data: AdminCreate):
    """
    Creates a new user with the 'admin' role.
    Only accessible by super admins.
    """
    hashed_password = bcrypt.hashpw(admin_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    roles = {role[1]: role[0] for role in db_utils.get_all_roles()}
    admin_role_id = roles.get("admin")
    
    if not admin_role_id:
        raise HTTPException(status_code=500, detail="Admin role not found in database.")

    user_id = db_utils.add_user(
        employee_id=admin_data.employee_id,
        employee_name=admin_data.employee_name,
        username=admin_data.username,
        hashed_password=hashed_password,
        role_id=admin_role_id,
        department_id=admin_data.department_id
    )
    
    if not user_id:
        raise HTTPException(status_code=409, detail="User with this Employee ID or Username already exists.")
        
    return {"message": f"Admin user '{admin_data.employee_name}' created successfully.", "user_id": user_id}

@router.put("/users/{employee_id}/role", summary="Change a User's Role")
def change_user_role(employee_id: str, role_update: UserRoleUpdate):
    """
    Updates the role of an existing user.
    A super admin cannot have their own role changed.
    """
    user = db_utils.get_user_by_employee_id(employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user[1] == 'SUPER001':
        raise HTTPException(status_code=403, detail="The primary super admin's role cannot be changed.")

    db_utils.update_user(employee_id, {"role_id": role_update.new_role_id})
    return {"message": f"Role for user {employee_id} has been updated."}

@router.get("/users", response_model=List[UserResponse], summary="List All Users")
def list_all_users():
    """
    Retrieves a list of all users in the system with their details.
    """
    users_raw = db_utils.get_all_users_with_details()
    return [
        UserResponse(
            id=u[0], employee_id=u[1], employee_name=u[2], username=u[3],
            role_name=u[4], department_name=u[5], is_active=u[6],
            face_count=u[7]  # Map the new face_count data
        ) for u in users_raw
    ]

@router.delete("/users/{employee_id}", summary="Delete a User")
def delete_user_account(employee_id: str):
    """
    Deletes a user account from the system.
    The primary super admin account cannot be deleted.
    """
    if employee_id == 'SUPER001':
        raise HTTPException(status_code=403, detail="The primary super admin account cannot be deleted.")
    
    db_utils.delete_user(employee_id)
    
    # Return a 200 OK response with a JSON body
    return {"message": f"User {employee_id} deleted successfully."}

# --- Camera and Tripwire Configuration Endpoints ---

@router.post("/cameras", status_code=status.HTTP_201_CREATED, summary="Add a New Camera")
def add_new_camera(camera_data: CameraCreate):
    """
    Adds a new camera to the system and configures its initial tripwires.
    """
    cam_id = db_utils.add_camera(
        name=camera_data.camera_name,
        cam_type=camera_data.camera_type,
        stream_url=camera_data.stream_url,
        res_w=camera_data.resolution_w,
        res_h=camera_data.resolution_h,
        fps=camera_data.fps,
        gpu_id=camera_data.gpu_id,
        user=camera_data.username,
        pw=camera_data.encrypted_password
    )
    if not cam_id:
        raise HTTPException(status_code=500, detail="Failed to create the camera in the database.")
    
    for tripwire in camera_data.tripwires:
        db_utils.add_tripwire(cam_id, **tripwire.dict())
        
    return {"message": "Camera and tripwires added successfully.", "camera_id": cam_id}

@router.put("/cameras/{camera_id}", summary="Update Camera Settings")
def update_camera_settings(camera_id: int, camera_update: CameraUpdate):
    """
    Updates the settings for an existing camera.
    """
    update_data = camera_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided.")
    
    db_utils.update_camera(camera_id, update_data)
    return {"message": f"Camera {camera_id} updated successfully."}

@router.delete("/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Camera")
def delete_camera_from_system(camera_id: int):
    """
    Deletes a camera and its associated tripwires from the system.
    """
    db_utils.delete_camera(camera_id)
    return

@router.post("/cameras/{camera_id}/tripwires", status_code=status.HTTP_201_CREATED, summary="Add a Tripwire to a Camera")
def add_tripwire_to_camera(camera_id: int, tripwire_data: TripwireCreate):
    """
    Adds a new tripwire to an existing camera.
    """
    tw_id = db_utils.add_tripwire(camera_id, **tripwire_data.dict())
    if not tw_id:
        raise HTTPException(status_code=500, detail="Failed to add tripwire.")
    return {"message": "Tripwire added successfully.", "tripwire_id": tw_id}

@router.put("/cameras/tripwires/{tripwire_id}", summary="Update a Tripwire")
def update_tripwire_settings(tripwire_id: int, tripwire_update: TripwireUpdate):
    """
    Updates the settings for an existing tripwire.
    """
    update_data = tripwire_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided.")
        
    db_utils.update_tripwire(tripwire_id, update_data)
    return {"message": f"Tripwire {tripwire_id} updated successfully."}

@router.delete("/cameras/tripwires/{tripwire_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Tripwire")
def delete_tripwire_from_system(tripwire_id: int):
    """
    Deletes a tripwire from the system.
    """
    db_utils.delete_tripwire(tripwire_id)
    return

# --- System Settings Endpoints ---

@router.get("/settings", summary="Get All System Settings")
def get_all_system_settings():
    """
    Retrieves all current system configuration settings.
    """
    return db_utils.get_system_settings()

@router.put("/settings", summary="Update a System Setting")
def update_a_system_setting(setting: SystemSettingUpdate):
    """
    Updates a single system setting in the database.
    """
    db_utils.update_system_setting(
        setting_key=setting.setting_key,
        setting_value=setting.setting_value,
        data_type=setting.data_type
    )
    return {"message": f"Setting '{setting.setting_key}' has been updated."}
@router.get("/cameras/{camera_id}/tripwires", summary="Get all tripwires for a camera")
def get_camera_tripwires(camera_id: int):
    """
    Retrieves a list of all tripwires for a specific camera.
    """
    return db_utils.get_tripwires_for_camera(camera_id)