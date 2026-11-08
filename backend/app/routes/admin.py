"""
Administrator Endpoints: Complaint Management, Lifecycle Status Updates,
Department-based Access Control, and Real-Time Dashboard Statistics.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.models import Complaint, ComplaintHistory, User, Department
from ..schemas.schemas import ComplaintOut, ComplaintDetail, ComplaintStatusUpdate
from ..services.notification_service import create_notification
from ..utils.file_utils import save_upload_image
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    Computes genuine real-time aggregated metrics from database records.
    Department admins receive filtered metrics for their department unless superadmin.
    """
    query = db.query(Complaint)
    if current_user.role == "admin" and current_user.department_id:
        query = query.filter(Complaint.assigned_department_id == current_user.department_id)

    total_complaints = query.count()
    pending = query.filter(Complaint.status.in_(["Submitted", "Assigned"])).count()
    in_progress = query.filter(Complaint.status == "In Progress").count()
    resolved = query.filter(Complaint.status == "Resolved").count()
    rejected = query.filter(Complaint.status == "Rejected").count()

    critical = query.filter(Complaint.severity == "Critical").count()
    high = query.filter(Complaint.severity == "High").count()
    medium = query.filter(Complaint.severity == "Medium").count()
    low = query.filter(Complaint.severity == "Low").count()

    # Category breakdown
    cat_counts = (
        query.with_entities(Complaint.predicted_category, func.count(Complaint.id))
        .group_by(Complaint.predicted_category)
        .all()
    )
    category_data = {cat: count for cat, count in cat_counts}

    # Department breakdown (across all complaints if superadmin)
    dept_query = db.query(Department.department_name, func.count(Complaint.id)).outerjoin(
        Complaint, Complaint.assigned_department_id == Department.id
    ).group_by(Department.department_name).all()
    dept_data = {name: count for name, count in dept_query}

    # Status distribution
    status_data = {
        "Submitted": query.filter(Complaint.status == "Submitted").count(),
        "Assigned": query.filter(Complaint.status == "Assigned").count(),
        "In Progress": in_progress,
        "Resolved": resolved,
        "Rejected": rejected
    }

    # Recent complaints
    recent_complaints = query.order_by(Complaint.created_at.desc()).limit(8).all()
    recent_list = []
    for c in recent_complaints:
        out = ComplaintOut.from_orm(c)
        out.citizen_name = c.citizen.name if c.citizen else None
        out.department_name = c.department.department_name if c.department else None
        recent_list.append(out)

    return {
        "total_complaints": total_complaints,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "rejected": rejected,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "category_distribution": category_data,
        "department_distribution": dept_data,
        "status_distribution": status_data,
        "severity_distribution": {
            "Critical": critical,
            "High": high,
            "Medium": medium,
            "Low": low
        },
        "recent_complaints": recent_list
    }


@router.get("/complaints", response_model=List[ComplaintOut])
def list_admin_complaints(
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    department_id: Optional[int] = None,
    village_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Returns filtered complaints list.
    Department admins only see complaints assigned to their department unless superadmin.
    """
    query = db.query(Complaint)

    if current_user.role == "admin" and current_user.department_id:
        query = query.filter(Complaint.assigned_department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Complaint.assigned_department_id == department_id)

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if category_filter:
        query = query.filter(Complaint.predicted_category == category_filter)
    if severity_filter:
        query = query.filter(Complaint.severity == severity_filter)
    if village_filter:
        query = query.filter(Complaint.village.ilike(f"%{village_filter}%"))

    complaints = query.order_by(Complaint.created_at.desc()).all()

    results = []
    for c in complaints:
        out = ComplaintOut.from_orm(c)
        out.citizen_name = c.citizen.name if c.citizen else None
        out.citizen_email = c.citizen.email if c.citizen else None
        out.citizen_phone = c.citizen.phone if c.citizen else None
        out.department_name = c.department.department_name if c.department else None
        results.append(out)

    return results


@router.put("/complaints/{id}/status", response_model=ComplaintDetail)
async def update_complaint_status(
    id: int,
    status: str = Form(...),
    comment: Optional[str] = Form(None),
    assigned_department_id: Optional[int] = Form(None),
    resolution_notes: Optional[str] = Form(None),
    resolution_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Updates complaint status, records audit history with timestamp,
    handles resolution photograph upload, and notifies the citizen.
    """
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Authorization check for department admin
    if current_user.role == "admin" and current_user.department_id:
        if complaint.assigned_department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Unauthorized: Complaint belongs to another department")

    old_status = complaint.status
    complaint.status = status

    # Handle resolution photo if marked Resolved or provided
    if resolution_image and resolution_image.filename:
        res_img_path = save_upload_image(resolution_image, UPLOAD_DIR)
        complaint.resolution_image_path = res_img_path

    if resolution_notes:
        complaint.resolution_notes = resolution_notes

    if assigned_department_id is not None:
        complaint.assigned_department_id = assigned_department_id

    # Add audit history
    history_entry = ComplaintHistory(
        complaint_id=complaint.id,
        old_status=old_status,
        new_status=status,
        comment=comment or f"Status changed from {old_status} to {status}.",
        updated_by=current_user.id
    )
    db.add(history_entry)
    db.commit()
    db.refresh(complaint)

    # Dispatch notification to citizen
    notif_msg = f"Update on complaint #{complaint.complaint_id}: Status changed to '{status}' by {current_user.name}."
    if comment:
        notif_msg += f" Note: {comment}"
    create_notification(db, complaint.citizen_id, notif_msg, complaint.id)

    out = ComplaintDetail.from_orm(complaint)
    out.citizen_name = complaint.citizen.name if complaint.citizen else None
    out.citizen_email = complaint.citizen.email if complaint.citizen else None
    out.citizen_phone = complaint.citizen.phone if complaint.citizen else None
    out.department_name = complaint.department.department_name if complaint.department else None

    for h in out.history:
        author = db.query(User).filter(User.id == h.updated_by).first()
        h.author_name = author.name if author else "Administrator"

    return out
