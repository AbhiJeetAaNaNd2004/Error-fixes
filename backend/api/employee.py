# api/employee.py

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from typing import List
import cv2
import numpy as np
import base64

from db import db_utils
from api.auth import require_role, get_current_user, TokenData
from schemas.employee import AttendanceRecord
from schemas.admin import FaceImageResponse # Re-use this schema
from dependencies import app_state # To access the face analyzer

router = APIRouter(
    prefix="/employee",
    tags=["Employee"],
    # This dependency ensures that a user must be logged in to access these endpoints.
    # The logic within each endpoint will further filter data to the specific user.
    dependencies=[Depends(require_role(["employee", "admin", "super_admin"]))]
)

@router.get("/me/attendance", response_model=List[AttendanceRecord], summary="Get My Attendance Records")
async def get_my_attendance_records(
    current_user: TokenData = Depends(get_current_user),
    limit: int = 100
):
    """
    Retrieves the attendance records for the currently authenticated user.
    An employee can only see their own records.
    """
    # The get_current_user dependency gives us the logged-in user's token data.
    # We use the username from the token to find their user details in the database.
    user_db_data = db_utils.get_user_for_login(current_user.username)
    
    if not user_db_data:
        raise HTTPException(status_code=404, detail="Current user not found in database.")
        
    user_id = user_db_data[0] # The first element returned is the user's internal ID.

    # Fetch attendance records specifically for this user_id
    records_raw = db_utils.get_attendance_for_user(user_id, limit=limit)
    
    # Convert the raw database tuples into Pydantic model instances
    return [
        AttendanceRecord(
            id=rec[0],
            event_type=rec[1],
            event_timestamp=rec[2],
            camera_name=rec[3],
            source=rec[4]
        ) for rec in records_raw
    ]

@router.get("/me/status", summary="Get My Current Work Status")
async def get_my_status(current_user: TokenData = Depends(get_current_user)):
    """
    Retrieves the most recent attendance event to determine the user's
    current work status (e.g., 'checked_in' or 'checked_out').
    """
    user_db_data = db_utils.get_user_for_login(current_user.username)
    if not user_db_data:
        raise HTTPException(status_code=404, detail="Current user not found in database.")
        
    user_id = user_db_data[0]
    
    # Get the single most recent record
    latest_records = db_utils.get_attendance_for_user(user_id, limit=1)
    
    if not latest_records:
        return {"status": "no_records_found", "last_event": None}
    
    last_event = latest_records[0]
    # The event_type of the most recent record determines the status
    status = "checked_in" if last_event[1] == "check_in" else "checked_out"
    
    return {"status": status, "last_event_time": last_event[2]}

@router.get("/me/profile-picture", summary="Get My Profile Picture")
async def get_my_profile_picture(current_user: TokenData = Depends(get_current_user)):
    """Retrieves the designated profile picture for the current user."""
    user_db_data = db_utils.get_user_for_login(current_user.username)
    if not user_db_data:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user_id = user_db_data[0]
    image_data = db_utils.get_profile_picture(user_id)

    if not image_data:
        raise HTTPException(status_code=404, detail="Profile picture not set.")

    return {"source_image": base64.b64encode(image_data).decode('utf-8')}

@router.put("/me/profile-picture/{embedding_id}", summary="Set an Existing Image as Profile Picture")
async def set_my_profile_picture(embedding_id: int, current_user: TokenData = Depends(get_current_user)):
    """Sets one of the user's existing face images as their profile picture."""
    user_db_data = db_utils.get_user_for_login(current_user.username)
    if not user_db_data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user_id = user_db_data[0]
    success = db_utils.set_profile_picture(user_id, embedding_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to set profile picture.")
    
    return {"message": "Profile picture updated successfully."}

@router.post("/me/profile-picture", summary="Upload a New Profile Picture")
async def upload_my_profile_picture(
    current_user: TokenData = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """Uploads a new image, creates an embedding, and sets it as the profile picture."""
    user_db_data = db_utils.get_user_for_login(current_user.username)
    if not user_db_data:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user_id = user_db_data[0]
    
    # Process the uploaded image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    face_analyzer = app_state["tracker"].apps[0]
    faces = face_analyzer.get(img)

    if len(faces) != 1:
        raise HTTPException(status_code=400, detail="Image must contain exactly one face.")

    embedding = faces[0].embedding
    
    # Add the new embedding to the database
    embedding_id = db_utils.add_face_embedding(
        user_id=user_id,
        embedding_vector=embedding,
        image_bytes=contents,
        embedding_type='profile' # Use a distinct type
    )

    if not embedding_id:
        raise HTTPException(status_code=500, detail="Failed to save new face embedding.")
    
    # Set the newly added image as the profile picture
    db_utils.set_profile_picture(user_id, embedding_id)

    return {"message": "Profile picture uploaded and set successfully.", "embedding_id": embedding_id}

