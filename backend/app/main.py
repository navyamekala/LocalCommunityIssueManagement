"""
FastAPI Main Application Entry Point.
AI-Based Local Community Issue Reporting and Management System Using DistilBERT.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base, SessionLocal
from .models.models import Department, User, Complaint, ComplaintHistory, ModelPrediction
from .services.auth_service import hash_password
from .routes import auth, complaints, admin, departments, ml, notifications
from .ml.predict import DistilBERTIssuePredictor


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def seed_database():
    """Initializes standard civic departments, admin accounts, demo citizen, and initial seed issues."""
    db = SessionLocal()
    try:
        # 1. Seed Civic Departments
        standard_departments = [
            ("Roads Department", "Responsible for potholes, damaged asphalt, road collapses, and pavement repairs"),
            ("Drainage Department", "Responsible for stormwater drains, sewer lines, waterlogging, and culvert blockages"),
            ("Electrical Department", "Responsible for non-functional streetlights, broken poles, live wires, and electrical safety"),
            ("Public Works Department", "Responsible for municipal infrastructure, public buildings, bridges, and facility defects"),
            ("Gardening Department", "Responsible for roadside vegetation trimming, overgrown trees, and public parks"),
            ("Traffic and Safety Department", "Responsible for road visibility, traffic signs, convex mirrors, and pedestrian safety"),
            ("Sanitation / Public Area Management", "Responsible for illegal garbage dumping, littering, abandoned items, and waste cleanup")
        ]

        dept_map = {}
        for name, desc in standard_departments:
            dept = db.query(Department).filter(Department.department_name == name).first()
            if not dept:
                dept = Department(department_name=name, description=desc)
                db.add(dept)
                db.commit()
                db.refresh(dept)
            dept_map[name] = dept

        # 2. Seed Super Admin
        super_admin = db.query(User).filter(User.email == "admin@community.gov.in").first()
        if not super_admin:
            super_admin = User(
                name="Central Administrator",
                email="admin@community.gov.in",
                phone="9876543210",
                password_hash=hash_password("Admin@123"),
                village="Headquarters",
                address="District Administrative Complex",
                role="superadmin"
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)

        # 3. Seed Department Admins
        dept_admins_config = [
            ("roads.admin@community.gov.in", "Roads Department Officer", "Roads Department"),
            ("drainage.admin@community.gov.in", "Drainage Department Officer", "Drainage Department"),
            ("electrical.admin@community.gov.in", "Electrical Department Officer", "Electrical Department"),
            ("pwd.admin@community.gov.in", "Public Works Officer", "Public Works Department"),
            ("gardening.admin@community.gov.in", "Gardening Department Officer", "Gardening Department"),
            ("traffic.admin@community.gov.in", "Traffic Safety Officer", "Traffic and Safety Department"),
            ("sanitation.admin@community.gov.in", "Sanitation Department Officer", "Sanitation / Public Area Management")
        ]

        for email, name, dept_name in dept_admins_config:
            existing_adm = db.query(User).filter(User.email == email).first()
            dept_obj = dept_map.get(dept_name)
            if not existing_adm:
                adm = User(
                    name=name,
                    email=email,
                    phone="9876500000",
                    password_hash=hash_password("Admin@123"),
                    village="District HQ",
                    address=f"{dept_name} Office",
                    role="admin",
                    department_id=dept_obj.id if dept_obj else None
                )
                db.add(adm)
                db.commit()
                if dept_obj and not dept_obj.admin_id:
                    dept_obj.admin_id = adm.id
                    db.commit()

        # 4. Seed Demo Citizen
        demo_citizen = db.query(User).filter(User.email == "citizen@example.com").first()
        if not demo_citizen:
            demo_citizen = User(
                name="Ramesh Kumar",
                email="citizen@example.com",
                phone="9123456780",
                password_hash=hash_password("Citizen@123"),
                village="Tadepalligudem",
                address="Near Gandhi Statue, Ward 4",
                role="citizen"
            )
            db.add(demo_citizen)
            db.commit()
            db.refresh(demo_citizen)

        # 5. Seed Initial Complaints if table is empty
        if db.query(Complaint).count() == 0:
            initial_issues = [
                {
                    "title": "Large dangerous pothole near Tadepalligudem bus stop",
                    "description": "A very large deep pothole has formed in the middle of the bus stop road causing severe traffic obstruction and bike accidents.",
                    "lat": 16.8124, "lng": 81.5284, "village": "Tadepalligudem", "landmark": "Opposite Main Bus Stand",
                    "cat": "Road Damage", "conf": 0.98, "dept": "Roads Department", "sev": "High", "rsn": "Significant disruption or infrastructure risk detected: 'large pothole'", "status": "In Progress"
                },
                {
                    "title": "Drainage water overflowing near village school",
                    "description": "Dirty drainage water is overflowing onto the walkway right in front of the village primary school. Children are unable to cross and bad smell is spreading.",
                    "lat": 16.8190, "lng": 81.5320, "village": "Tadepalligudem", "landmark": "ZPH High School Gate",
                    "cat": "Clogging", "conf": 0.96, "dept": "Drainage Department", "sev": "Critical", "rsn": "Hazardous community condition near sensitive public infrastructure (school/hospital)", "status": "Submitted"
                },
                {
                    "title": "Streetlights not working on main market road",
                    "description": "Non-functional streetlights along the 500m market road stretch causing total darkness at night and increasing safety risk for pedestrians.",
                    "lat": 16.8150, "lng": 81.5250, "village": "Tadepalligudem", "landmark": "Market Complex",
                    "cat": "Lamp Breakage", "conf": 0.99, "dept": "Electrical Department", "sev": "Medium", "rsn": "Public lighting maintenance required for night safety", "status": "Assigned"
                },
                {
                    "title": "Garbage accumulating near village fish market",
                    "description": "Uncollected garbage and rotten waste left on the side of the street for over four days, attracting stray animals and creating foul odor.",
                    "lat": 16.8105, "lng": 81.5295, "village": "Tadepalligudem", "landmark": "Weekly Bazaar Ground",
                    "cat": "Leaving", "conf": 0.97, "dept": "Sanitation / Public Area Management", "sev": "Medium", "rsn": "Public area cleanup or waste collection scheduled maintenance", "status": "In Progress"
                },
                {
                    "title": "Overgrown trees and roadside bushes blocking view",
                    "description": "Thick tree branches and overgrown vegetation are completely blocking the sharp road curve visibility, posing serious danger to vehicles.",
                    "lat": 16.8220, "lng": 81.5360, "village": "Tadepalligudem", "landmark": "Canal Road Turn",
                    "cat": "Overgrowth", "conf": 0.95, "dept": "Gardening Department", "sev": "High", "rsn": "Significant disruption or infrastructure risk detected: 'blind curve'", "status": "Submitted"
                },
                {
                    "title": "Broken bench and cracked shade structure at public park",
                    "description": "The concrete bench is broken into pieces and the iron shade beam has detached and is leaning dangerously at the village children park.",
                    "lat": 16.8175, "lng": 81.5230, "village": "Tadepalligudem", "landmark": "Gram Panchayat Park",
                    "cat": "Facility Defect", "conf": 0.94, "dept": "Public Works Department", "sev": "Medium", "rsn": "Public facility defect requiring maintenance inspection", "status": "Resolved"
                }
            ]

            for idx, item in enumerate(initial_issues, 1):
                dept_obj = dept_map.get(item["dept"])
                c = Complaint(
                    complaint_id=f"CMP-20261030-{1000+idx}",
                    citizen_id=demo_citizen.id,
                    title=item["title"],
                    description=item["description"],
                    latitude=item["lat"],
                    longitude=item["lng"],
                    village=item["village"],
                    address=f"{item['landmark']}, {item['village']}",
                    landmark=item["landmark"],
                    predicted_category=item["cat"],
                    confidence_score=item["conf"],
                    assigned_department_id=dept_obj.id if dept_obj else None,
                    severity=item["sev"],
                    severity_reason=item["rsn"],
                    status=item["status"]
                )
                db.add(c)
                db.commit()
                db.refresh(c)

                h = ComplaintHistory(
                    complaint_id=c.id,
                    old_status=None,
                    new_status=item["status"],
                    comment=f"Initial seeded civic report for demonstration. Classified as {item['cat']}.",
                    updated_by=super_admin.id
                )
                db.add(h)
                p = ModelPrediction(
                    complaint_id=c.id,
                    predicted_category=item["cat"],
                    confidence=item["conf"],
                    model_version="DistilBERT-v1.0"
                )
                db.add(p)
                db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables created and database seeded
    Base.metadata.create_all(bind=engine)
    seed_database()
    # Preload DistilBERT predictor into memory
    DistilBERTIssuePredictor.get_instance()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="AI Local Community Issue Management Portal (DistilBERT)",
    description="End-to-end Citizen Problem Reporting, DistilBERT Classification, Severity Scoring & Administrative Workflow System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(admin.router)
app.include_router(departments.router)
app.include_router(ml.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    return {
        "status": "online",
        "system": "AI-Based Local Community Issue Reporting and Management System Using DistilBERT",
        "version": "1.0.0",
        "docs_url": "/docs"
    }
