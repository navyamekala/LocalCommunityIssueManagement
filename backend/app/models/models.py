"""
SQLAlchemy Relational Database Models for Local Community Issue Management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)
    village = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    role = Column(String(30), default="citizen", nullable=False)  # "citizen", "admin", "superadmin"
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    history_entries = relationship("ComplaintHistory", back_populates="author", foreign_keys="ComplaintHistory.updated_by")
    department = relationship("Department", back_populates="members", foreign_keys=[department_id])


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(120), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    members = relationship("User", back_populates="department", foreign_keys="User.department_id")
    complaints = relationship("Complaint", back_populates="department")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, index=True, nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    image_path = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String(255), nullable=True)
    village = Column(String(100), nullable=True)
    landmark = Column(String(150), nullable=True)
    predicted_category = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    assigned_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    severity = Column(String(50), nullable=False)  # "Critical", "High", "Medium", "Low"
    severity_reason = Column(Text, nullable=True)
    status = Column(String(50), default="Submitted", nullable=False)  # "Submitted", "Assigned", "In Progress", "Resolved", "Rejected"
    resolution_image_path = Column(String(500), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    department = relationship("Department", back_populates="complaints")
    history = relationship("ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintHistory.updated_at")
    notifications = relationship("Notification", back_populates="complaint", cascade="all, delete-orphan")
    predictions = relationship("ModelPrediction", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    complaint = relationship("Complaint", back_populates="history")
    author = relationship("User", back_populates="history_entries", foreign_keys=[updated_by])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")
    complaint = relationship("Complaint", back_populates="notifications")


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    predicted_category = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), default="DistilBERT-v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    complaint = relationship("Complaint", back_populates="predictions")
