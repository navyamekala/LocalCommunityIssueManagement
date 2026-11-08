# System Architecture: AI-Based Local Community Issue Reporting and Management System (DistilBERT)

Based on the proposed system design reference (`system_architecture.png`) and the Kano et al. (2019) research framework.

---

## 1. High-Level Architectural Overview

The application follows a decoupled modern multi-tier client-server architecture:

```
[ Citizens (Web / Mobile) ]                [ Administrative Authorities / Officers ]
      │                                                     │
      ├── Submit Problem (Photo + GPS Location)            ├── Review Dispatched Complaints
      ├── Interactive Map Pinning                          ├── Update Status & Inspection Notes
      ├── Live Timeline Tracking                           ├── Upload Resolution Photographs
      └── In-App Notifications                             └── Monitor Real-Time Analytics
               │                                                    │
               ▼                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           React 19 + Vite Frontend                               │
│              (Tailwind CSS, Leaflet OpenStreetMap, Axios, Lucide)               │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ RESTful APIs / JWT Auth
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             FastAPI Application Server                          │
│     - Authentication & RBAC Service (Citizen / Dept Admin / Super Admin)        │
│     - Complaint Registration & Management Engine                                │
│     - In-App Notification Dispatcher                                            │
│     - Audit & Complaint History Tracking Service                                │
│     - Static Media & File Validation Service                                    │
└────────────────────────┬───────────────────────────────┬────────────────────────┘
                         │                               │
                         ▼                               ▼
       ┌───────────────────────────────────┐   ┌──────────────────────────────────┐
       │     AI / NLP Module (DistilBERT)  │   │        Database Layer            │
       │  - DistilBERT Transformer         │   │   - SQLite / PostgreSQL          │
       │  - Tokenizer (distilbert-uncased) │   │   - Users & Roles (RBAC)         │
       │  - 7 Canonical Problem Classes    │   │   - Departments (7 Core Depts)   │
       │  - Softmax Confidence Scoring     │   │   - Complaints & History Log     │
       │  - Rule-Based Severity Engine     │   │   - In-App Notifications         │
       │  - Department Routing Engine      │   │   - Model Predictions Audit      │
       └───────────────────────────────────┘   └──────────────────────────────────┘
```

---

## 2. Component Details

### A. Citizen (User) Module
- **Problem Submission**: Citizens report civic defects by supplying a Title, Description, Photograph, and Geolocation.
- **Geolocation Service**: Dual mechanism:
  1. *Browser HTML5 Geolocation API*: Automatically detects device GPS coordinates.
  2. *Interactive Leaflet Map*: Allows manually clicking anywhere on the map to drop and reposition a pin.
- **Lifecycle Tracking**: Citizens track complaints in real-time across 5 stages:
  `Submitted` → `AI Classified` → `Assigned to Department` → `In Progress` → `Resolved`.
- **In-App Notifications**: Real-time updates delivered whenever an officer reviews or updates a complaint.

### B. AI / NLP Classification Module (DistilBERT)
- **Model**: `distilbert-base-uncased` fine-tuned for multi-class sequence classification.
- **Input Representation**: Synthesized text combining `Title` + `Description`.
- **Classification Output**: 7 canonical problem categories derived from citizen report text mining research.
- **Confidence Estimation**: Softmax probability over all 7 classes. Low-confidence predictions (< 40%) trigger a "Needs Manual Review" safety fallback.
- **Severity Assessment Engine**: Transparent rule-based heuristic evaluating hazard urgency indicators, life safety risks, and infrastructure sensitivity (schools/hospitals).

### C. Backend Application Server (FastAPI)
- **Architecture**: Modular FastAPI application with Pydantic schemas, SQLAlchemy ORM, and dependency injection.
- **Role-Based Access Control (RBAC)**:
  - *Citizen*: Can report issues and view only their own complaints and notifications.
  - *Department Administrator*: Can view and update complaints assigned specifically to their department.
  - *Central Super Administrator*: Unrestricted oversight over all civic departments and users.
- **Complaint History Audit**: Every status change is immutably logged with timestamp, administrator ID, and explanatory comments.

### D. Administrative Department Module
- **Department Routing**:
  - `Road Damage` → Roads Department
  - `Clogging` → Drainage Department
  - `Lamp Breakage` → Electrical Department
  - `Facility Defect` → Public Works Department
  - `Overgrowth` → Gardening Department
  - `Invisibility` → Traffic and Safety Department
  - `Leaving` → Sanitation / Public Area Management
- **Status Lifecycle Control**: Officers update status (`Assigned`, `In Progress`, `Resolved`, `Rejected`), enter inspection remarks, and attach resolution photographs as visual evidence.

### E. Frontend User Interface
- Built with React, Vite, Tailwind CSS, and Leaflet.
- Fully responsive, mobile-first design with high contrast, accessible typography, and intuitive icons suited for rural citizens and civic staff.
