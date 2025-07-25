# api/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from typing import List
import bcrypt
import cv2
import numpy as np
import base64
from pydantic import BaseModel

from db import db_utils
from api.auth import require_role
from schemas.admin import EmployeeCreate, FaceImageResponse, UserInfo
from dependencies import app_state

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    # This dependency applies the role check to all routes in this router.
    # Both 'admin' and 'super_admin' can access these endpoints.
    dependencies=[Depends(require_role(["admin", "super_admin"]))]
)

# NEW: Schema for user department assignment
class UserDepartmentAssignment(BaseModel):
    user_id: int
    department_id: int

def get_face_enroller():
    """Dependency to get the face enroller from the app state."""
    # The FaceEnroller is part of the FaceTrackingSystem, but for clarity,
    # we can imagine it as a separate component for enrollment tasks.
    # Here, we'll just use the FaceAnalysis model from the tracker.
    tracker = app_state.get("tracker")
    if not tracker or not hasattr(tracker, 'apps'):
        raise HTTPException(status_code=503, detail="Face analysis service not available.")
    # Return the FaceAnalysis instance for GPU 0 (or adapt if needed)
    return tracker.apps[0]


@router.post("/users/create/employee", response_model=UserInfo, status_code=status.HTTP_201_CREATED, summary="Create a new Employee User")
def create_employee_user(employee_data: EmployeeCreate):
    """
    Creates a new user with the 'employee' role.
    Accessible by admins and super admins.
    """
    hashed_password = bcrypt.hashpw(employee_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    roles = {role[1]: role[0] for role in db_utils.get_all_roles()}
    employee_role_id = roles.get("employee")
    
    if not employee_role_id:
        raise HTTPException(status_code=500, detail="Employee role not found in database.")

    user_id = db_utils.add_user(
        employee_id=employee_data.employee_id,
        employee_name=employee_data.employee_name,
        username=employee_data.username,
        hashed_password=hashed_password,
        role_id=employee_role_id,
        department_id=employee_data.department_id
    )
    
    if not user_id:
        raise HTTPException(status_code=409, detail="User with this Employee ID or Username already exists.")
        
    return UserInfo(id=user_id, employee_id=employee_data.employee_id, employee_name=employee_data.employee_name)

@router.post("/faces/enroll/{user_id}", summary="Enroll new faces for a user")
async def enroll_faces_for_user(
    user_id: int,
    images: List[UploadFile] = File(..., description="Upload 3 to 5 images of the user's face."),
    face_analyzer = Depends(get_face_enroller)
):
    """
    Enrolls new face images for an existing user. Requires image file uploads.
    """
    if not (3 <= len(images) <= 5):
        raise HTTPException(status_code=400, detail="Please upload between 3 and 5 images for enrollment.")

    saved_embeddings = 0
    for image_file in images:
        contents = await image_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            continue

        faces = face_analyzer.get(img)

        if len(faces) != 1:
            # Skip images that don't have exactly one face
            continue

        embedding = faces[0].embedding
        
        embedding_id = db_utils.add_face_embedding(
            user_id=user_id,
            embedding_vector=embedding,
            image_bytes=contents,
            embedding_type='enrollment'
        )
        if embedding_id:
            saved_embeddings += 1

    if saved_embeddings == 0:
        raise HTTPException(status_code=400, detail="No valid faces were detected in the uploaded images.")

    return {"message": f"Successfully saved {saved_embeddings} new face embeddings for user ID {user_id}."}


@router.get("/faces/{user_id}", response_model=List[FaceImageResponse], summary="Get all face images for a user")
def get_user_faces(user_id: int):
    """
    Retrieves all enrolled face images for a specific user.
    """
    images = db_utils.get_user_face_images(user_id)
    
    # Convert the image bytes to a Base64 string for JSON compatibility
    return [
        FaceImageResponse(
            id=img[0], 
            source_image=base64.b64encode(img[1]).decode('utf-8')
        ) for img in images
    ]


@router.delete("/faces/{embedding_id}", summary="Delete a face embedding")
def delete_face_embedding(embedding_id: int):
    """
    Deletes a specific face embedding from the database.
    """
    result = db_utils.delete_face_embedding(embedding_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Embedding not found.")
    
    # Return a success response with a 200 OK status and a JSON body
    return {"message": "Embedding deleted successfully."}

# NEW: Endpoint for assigning user to department
@router.put("/users/department", summary="Assign user to department")
def assign_user_department(assignment: UserDepartmentAssignment):
    """
    Assigns a user to a specific department.
    Accessible by admins and super admins.
    """
    try:
        db_utils.update_user_department(assignment.user_id, assignment.department_id)
        return {"message": f"User {assignment.user_id} successfully assigned to department {assignment.department_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign user to department: {str(e)}")

# In api/admin.py
from schemas.employee import AttendanceRecord # You may need to create/adjust this schema

@router.get("/attendance", summary="Get All Attendance Records")
def get_all_attendance():
    """
    Retrieves a list of all attendance records for all users.
    Accessible by admins and super admins.
    """
    records = db_utils.get_all_attendance_logs()
    # You'll need to map the raw records to a Pydantic model for the response
    return records