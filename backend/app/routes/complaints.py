"""
Citizen Complaint Submission, List, and Tracking Endpoints.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.models import Complaint, ComplaintHistory, ModelPrediction, Department, User
from ..schemas.schemas import ComplaintOut, ComplaintDetail
from ..ml.predict import DistilBERTIssuePredictor
from ..services.notification_service import create_notification
from ..utils.file_utils import save_upload_image
from .auth import get_current_user

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


def generate_complaint_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:5].upper()
    return f"CMP-{timestamp}-{random_suffix}"


@router.post("", response_model=ComplaintOut)
async def submit_complaint(
    title: str = Form(...),
    description: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    village: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    landmark: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a new citizen problem.
    Runs DistilBERT real-time classification, severity scoring, department assignment,
    saves history, and notifies the citizen.
    """
    # 1. Handle Image Upload if provided
    image_path = None
    if image and image.filename:
        image_path = save_upload_image(image, UPLOAD_DIR)

    # 2. Run DistilBERT NLP Prediction
    predictor = DistilBERTIssuePredictor.get_instance()
    prediction_result = predictor.predict(title, description)

    predicted_category = prediction_result["predicted_category"]
    confidence_score = prediction_result["confidence_score"]
    responsible_dept_name = prediction_result["responsible_department"]
    severity = prediction_result["severity"]
    severity_reason = prediction_result["severity_reason"]

    # 3. Locate Assigned Department
    dept = db.query(Department).filter(Department.department_name == responsible_dept_name).first()
    assigned_dept_id = dept.id if dept else None

    # 4. Create Complaint
    complaint_code = generate_complaint_id()
    new_complaint = Complaint(
        complaint_id=complaint_code,
        citizen_id=current_user.id,
        title=title,
        description=description,
        image_path=image_path,
        latitude=latitude,
        longitude=longitude,
        village=village or current_user.village or "Local Village",
        address=address or current_user.address,
        landmark=landmark,
        predicted_category=predicted_category,
        confidence_score=confidence_score,
        assigned_department_id=assigned_dept_id,
        severity=severity,
        severity_reason=severity_reason,
        status="Submitted"
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    # 5. Record Initial History Entry
    history_entry = ComplaintHistory(
        complaint_id=new_complaint.id,
        old_status=None,
        new_status="Submitted",
        comment=f"Complaint submitted by citizen. AI DistilBERT predicted category: '{predicted_category}' ({confidence_score*100:.1f}% confidence) and routed to {responsible_dept_name}.",
        updated_by=current_user.id
    )
    db.add(history_entry)

    # 6. Save ModelPrediction record
    model_record = ModelPrediction(
        complaint_id=new_complaint.id,
        predicted_category=predicted_category,
        confidence=confidence_score,
        model_version="DistilBERT-v1.0"
    )
    db.add(model_record)
    db.commit()

    # 7. Notify Citizen
    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Your complaint '{title}' was successfully registered with ID {complaint_code} and classified as '{predicted_category}'. Assigned to {responsible_dept_name}.",
        complaint_id=new_complaint.id
    )

    # Return serialized output with department name
    out = ComplaintOut.from_orm(new_complaint)
    out.citizen_name = current_user.name
    out.citizen_email = current_user.email
    out.citizen_phone = current_user.phone
    out.department_name = responsible_dept_name
    return out


@router.get("/my", response_model=List[ComplaintOut])
def get_my_complaints(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns all complaints submitted by the logged-in citizen."""
    complaints = db.query(Complaint).filter(Complaint.citizen_id == current_user.id).order_by(Complaint.created_at.desc()).all()
    results = []
    for c in complaints:
        out = ComplaintOut.from_orm(c)
        out.citizen_name = current_user.name
        out.citizen_email = current_user.email
        out.citizen_phone = current_user.phone
        out.department_name = c.department.department_name if c.department else None
        results.append(out)
    return results


@router.get("/tracking/{complaint_id}", response_model=ComplaintDetail)
def track_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """
    Public or citizen tracking endpoint: retrieves complaint timeline,
    location, resolution photo, and full lifecycle history.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint with ID '{complaint_id}' not found.")

    out = ComplaintDetail.from_orm(complaint)
    out.citizen_name = complaint.citizen.name if complaint.citizen else "Citizen"
    out.citizen_email = complaint.citizen.email if complaint.citizen else None
    out.citizen_phone = complaint.citizen.phone if complaint.citizen else None
    out.department_name = complaint.department.department_name if complaint.department else None

    # Populate history author names
    for h in out.history:
        author = db.query(User).filter(User.id == h.updated_by).first()
        h.author_name = author.name if author else "System"

    return out


@router.get("/{id}", response_model=ComplaintDetail)
def get_complaint_by_id(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Gets single complaint details with authorization checks."""
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Authorization: citizen can only view their own; admin can view
    if current_user.role == "citizen" and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this complaint")

    out = ComplaintDetail.from_orm(complaint)
    out.citizen_name = complaint.citizen.name if complaint.citizen else None
    out.citizen_email = complaint.citizen.email if complaint.citizen else None
    out.citizen_phone = complaint.citizen.phone if complaint.citizen else None
    out.department_name = complaint.department.department_name if complaint.department else None

    for h in out.history:
        author = db.query(User).filter(User.id == h.updated_by).first()
        h.author_name = author.name if author else "System"

    return out
