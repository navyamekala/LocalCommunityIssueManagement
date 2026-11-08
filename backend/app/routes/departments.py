"""
Department Management Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.models import Department, User
from ..schemas.schemas import DepartmentOut, DepartmentCreate
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/api/departments", tags=["Departments"])


@router.get("", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    """Returns all civic departments."""
    return db.query(Department).all()


@router.post("", response_model=DepartmentOut)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Allows administrators to create or register new departments."""
    existing = db.query(Department).filter(Department.department_name == dept_in.department_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")
    
    dept = Department(
        department_name=dept_in.department_name,
        description=dept_in.description,
        admin_id=dept_in.admin_id
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
