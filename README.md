# GramSetu AI: Local Community Issue Reporting and Management System Using DistilBERT

An end-to-end AI-powered web platform for reporting, classifying, tracking, and resolving citizen problems in villages and towns. Powered by a fine-tuned **DistilBERT** Transformer NLP model, **FastAPI** backend, and **React + Vite + Leaflet** interactive frontend.

---

## 🎓 Academic Project Credentials
- **Institution**: Sri Vasavi Engineering College (Autonomous), Pedatadepalli, Tadepalligudem - 534101, A.P. (Affiliated to JNTUK Kakinada)
- **Department**: Department of Computer Science and Engineering (Artificial Intelligence)
- **Academic Year**: 2026 - 2027 | **Batch No**: 8 | **Milestone**: Major Project Review-I
- **Project Title**: *Deep Learning-Based Classification of Local Citizen Complaints Using DistilBERT*
- **Project Guide**: **Dr. Jewaliddin Shaik**, Associate Professor, Dept. of CSE (AI)
- **Head of the Department**: **Dr. G. Loshma**, Professor & HOD
- **Project Associates (Students)**:
  1. **I. Teja Sri** — `24A85A4310`
  2. **M. Navya** — `23A81A43B5`
  3. **R. Nikhil** — `23A81A43C6`
  4. **A. Bhanu Sri** — `23A81A4368`

---

## 📄 Generated Project Documentation
- **Word Document (.docx)**: [`Deep_Learning_Classification_Local_Citizen_Complaints_Report.docx`](./Deep_Learning_Classification_Local_Citizen_Complaints_Report.docx) *(Full 10-chapter academic report matching official college standards with embedded evaluation plots, figures, and tables)*
- **PowerPoint Presentation (.pptx)**: [`Deep_Learning_Classification_Local_Citizen_Complaints_Presentation.pptx`](./Deep_Learning_Classification_Local_Citizen_Complaints_Presentation.pptx) *(16:9 widescreen presentation formatted for Major Project Review-I)*

---

## 🔬 Research Foundation & Base Paper
This project implements and expands upon the empirical problem taxonomy discovered in:
> **"A Method of Extracting and Classifying Local Community Problems from Citizen-Report Data using Text Mining"**  
> *Eiji Kano, Yoshikatsu Fujita, Kazuhiko Tsuda (Procedia Computer Science, Vol. 159, 2019, pp. 1347–1356)*

The research proves that citizen reports objectively cluster into **seven canonical problem categories** rather than traditional administrative silos:
1. **Road Damage** → Roads & Infrastructure Department
2. **Clogging** → Drainage & Sewerage Department
3. **Lamp Breakage** → Electrical & Street Lighting Department
4. **Facility Defect** → Public Works Department (PWD)
5. **Overgrowth** → Gardening & Horticulture Department
6. **Invisibility** → Traffic Signs & Road Safety Department
7. **Leaving** → Sanitation & Public Area Management Department

---

## 🛠️ Technology Stack

- **NLP / Deep Learning**: DistilBERT (`distilbert-base-uncased`), PyTorch, Hugging Face Transformers, Scikit-learn
- **Backend**: Python 3.12, FastAPI, SQLAlchemy ORM, SQLite database, JWT Authentication, Bcrypt
- **Frontend**: React 19, Vite, Tailwind CSS, Leaflet + OpenStreetMap, Lucide Icons, Axios
- **Visualization**: Matplotlib, Seaborn, Real-Time Interactive Testing Playground

---

## 🚀 Quick Start (Windows One-Click)

Simply double-click:
```cmd
run_project.bat
```
This batch script automatically launches the FastAPI backend on port 8000 and the Vite frontend on port 5173.

---

## 🔑 Pre-Configured Test Accounts

| Role | Email | Password | Scope |
|---|---|---|---|
| **Central Superadmin** | `admin@community.gov.in` | `Admin@123` | Unrestricted oversight across all departments & users |
| **Roads Dept Admin** | `roads.admin@community.gov.in` | `Admin@123` | Manages Road Damage & potholes |
| **Drainage Dept Admin**| `drainage.admin@community.gov.in` | `Admin@123` | Manages Clogging & overflowing drains |
| **Electrical Dept Admin**| `electrical.admin@community.gov.in` | `Admin@123` | Manages Lamp Breakage & dark streetlights |
| **PWD Officer** | `pwd.admin@community.gov.in` | `Admin@123` | Manages Facility Defects & public works |
| **Gardening Officer** | `gardening.admin@community.gov.in` | `Admin@123` | Manages Overgrowth & roadside branches |
| **Traffic Safety Officer**| `traffic.admin@community.gov.in` | `Admin@123` | Manages Invisibility & blind curve hazards |
| **Sanitation Officer** | `sanitation.admin@community.gov.in` | `Admin@123` | Manages Leaving & illegal garbage dumping |
| **Demo Citizen** | `citizen@example.com` | `Citizen@123` | Submits issues, tracks status, receives alerts |

*(One-click category login cards are also provided directly on the Login page).*

---

## 🔄 End-to-End Workflow

1. **Citizen Registration & Login**: Citizen signs up with name, email, phone, and village name.
2. **Problem Reporting**:
   - Title & detailed problem narrative.
   - Photograph upload or camera capture.
   - GPS Auto-Detection or clicking on the Leaflet interactive map.
3. **AI DistilBERT Engine**:
   - Evaluates complaint text.
   - Computes Softmax class probabilities and confidence score.
   - Flags low-confidence predictions (< 40%) for manual review.
   - Transparent rule-based severity rating (`Critical`, `High`, `Medium`, `Low`).
4. **Department Routing**: Dispatches the issue directly into the designated Department Officer queue.
5. **Field Inspection & Status Updates**:
   - Officer reviews issue on map and original photograph.
   - Changes status (`Assigned` → `In Progress` → `Resolved`).
   - Attaches resolution photo and remarks.
6. **Citizen Tracking & Alerts**:
   - Real-time in-app notification delivered to citizen.
   - Citizen tracks lifecycle timeline and views resolution photograph.
