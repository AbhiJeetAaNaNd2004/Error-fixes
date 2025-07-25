from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from db import db_utils
from api.auth import require_role

router = APIRouter(
    tags=["Departments"]
)

# --- Pydantic Models ---
class Department(BaseModel):
    id: int
    department_name: str

class DepartmentCreate(BaseModel):
    department_name: str

class UserDepartmentUpdate(BaseModel):
    user_id: int
    department_id: int

# --- Super Admin: Department CRUD ---
@router.get("/superadmin/departments", response_model=List[Department], dependencies=[Depends(require_role(["super_admin"]))])
def list_departments():
    departments_raw = db_utils.get_all_departments()
    # Adapting to the user's db_utils which returns tuples
    return [{"id": dept[0], "department_name": dept[1]} for dept in departments_raw]

@router.post("/superadmin/departments", response_model=Department, dependencies=[Depends(require_role(["super_admin"]))])
def create_department(department: DepartmentCreate):
    dept_id = db_utils.add_department(department.department_name)
    if not dept_id:
        raise HTTPException(status_code=400, detail="Department with this name may already exist.")
    return {"id": dept_id, "department_name": department.department_name}

@router.put("/superadmin/departments/{department_id}", dependencies=[Depends(require_role(["super_admin"]))])
def update_department_name(department_id: int, department: DepartmentCreate):
    db_utils.update_department(department_id, department.department_name)
    return {"message": "Department updated successfully."}

@router.delete("/superadmin/departments/{department_id}", dependencies=[Depends(require_role(["super_admin"]))])
def remove_department(department_id: int):
    db_utils.delete_department(department_id)
    return {"message": "Department deleted successfully."}

# --- Admin: Assign Department to User ---
@router.put("/admin/users/department", dependencies=[Depends(require_role(["admin", "super_admin"]))])
def assign_department(update: UserDepartmentUpdate):
    # This requires a new db_utils function
    db_utils.update_user_department(update.user_id, update.department_id)
    return {"message": "User's department updated successfully."}
