"""
Pydantic Schemas for Request Validation and Response Serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# --- Authentication & Users ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None
    role: Optional[str] = "citizen"
    department_id: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None
    role: str
    department_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


# --- Departments ---
class DepartmentCreate(BaseModel):
    department_name: str
    description: Optional[str] = None
    admin_id: Optional[int] = None


class DepartmentOut(BaseModel):
    id: int
    department_name: str
    description: Optional[str] = None
    admin_id: Optional[int] = None

    class Config:
        from_attributes = True


# --- Complaints ---
class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    village: Optional[str] = None
    address: Optional[str] = None
    landmark: Optional[str] = None


class ComplaintHistoryOut(BaseModel):
    id: int
    complaint_id: int
    old_status: Optional[str]
    new_status: str
    comment: Optional[str]
    updated_by: int
    author_name: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintOut(BaseModel):
    id: int
    complaint_id: str
    citizen_id: int
    citizen_name: Optional[str] = None
    citizen_email: Optional[str] = None
    citizen_phone: Optional[str] = None
    title: str
    description: str
    image_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    village: Optional[str] = None
    landmark: Optional[str] = None
    predicted_category: str
    confidence_score: float
    assigned_department_id: Optional[int] = None
    department_name: Optional[str] = None
    severity: str
    severity_reason: Optional[str] = None
    status: str
    resolution_image_path: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintDetail(ComplaintOut):
    history: List[ComplaintHistoryOut] = []


class ComplaintStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None
    assigned_department_id: Optional[int] = None
    resolution_notes: Optional[str] = None


# --- Notifications ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    complaint_id: Optional[int] = None
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- ML & Analytics ---
class PredictionRequest(BaseModel):
    title: str
    description: str


class PredictionResponse(BaseModel):
    predicted_category: str
    confidence_score: float
    probabilities: Dict[str, float]
    responsible_department: str
    severity: str
    severity_reason: str
    severity_score: float
    severity_method: str
    needs_manual_review: bool
