# Relational Database Schema Design

The application uses SQLAlchemy ORM configured for SQLite (development) and PostgreSQL (production).

---

## 1. Entity-Relationship Overview

```
 ┌──────────────┐          ┌────────────────────┐
 │  Department  │◄───┐    │    Complaint       │
 ├──────────────┤    │    ├────────────────────┤
 │ id (PK)      │    │    │ id (PK)            │
 │ name         │    │    │ complaint_id       │
 │ description  │    └───┼─ assigned_dept_id    │
 │ admin_id     │         │ citizen_id (FK)───┐│
 └──────▲───────┘         │ title              ││
        │                 │ description        ││
        │                 │ image_path         ││
        │                 │ latitude           ││
        │                 │ longitude          ││
        │                 │ predicted_category ││
        │                 │ confidence_score   ││
        │                 │ severity           ││
        │                 │ status             ││
        │                 │ resolution_photo   ││
        │                 │ created_at         ││
        │                 └─────────┬──────────┘│
        │                           │           │
 ┌──────┴───────┐         ┌─────────▼──────────┐│
 │    User      │◄────────┤  ComplaintHistory  ││
 ├──────────────┤         ├────────────────────┤│
 │ id (PK)      │         │ id (PK)            ││
 │ name         │         │ complaint_id (FK)  ││
 │ email        │         │ old_status         ││
 │ role         │         │ new_status         ││
 │ department_id│         │ comment            ││
 │ village      │         │ updated_by (FK)    ││
 └──────▲───────┘         └────────────────────┘│
        │                                       │
        │                 ┌────────────────────┐│
        │                 │   Notification     ││
        │                 ├────────────────────┤│
        └─────────────────┤ user_id (FK)       ││
                          │ complaint_id (FK)  ││
                          │ message            ││
                          │ is_read            ││
                          └────────────────────┘│
                                                │
                          ┌────────────────────┐│
                          │  ModelPrediction   ││
                          ├────────────────────┤│
                          │ complaint_id (FK)───┘
                          │ predicted_category │
                          │ confidence         │
                          │ model_version      │
                          └────────────────────┘
```

---

## 2. Table Specifications

### 1. `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | Unique user identifier |
| `name` | String(120) | Not Null | Citizen or officer full name |
| `email` | String(120) | Unique, Index | Login email address |
| `phone` | String(30) | Nullable | Contact phone number |
| `password_hash` | String(255) | Not Null | Bcrypt hashed password |
| `village` | String(100) | Nullable | Residential village/town |
| `address` | String(255) | Nullable | Street/ward address |
| `role` | String(30) | Not Null | `citizen`, `admin`, `superadmin` |
| `department_id` | Integer | FK (`departments.id`) | Assigned department for officers |
| `created_at` | DateTime | Default UTC | Registration timestamp |

### 2. `departments`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | Department ID |
| `department_name` | String(120) | Unique, Not Null | Municipal department title |
| `description` | String(255) | Nullable | Jurisdictional scope |
| `admin_id` | Integer | FK (`users.id`) | Head administrator ID |

### 3. `complaints`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | Internal primary key |
| `complaint_id` | String(50) | Unique, Index | Public tracking code (`CMP-YYYYMMDD-XXXX`) |
| `citizen_id` | Integer | FK (`users.id`) | Reporting citizen ID |
| `title` | String(255) | Not Null | Problem summary |
| `description` | Text | Not Null | Comprehensive narrative |
| `image_path` | String(500) | Nullable | Uploaded photo path |
| `latitude` | Float | Nullable | GPS latitude coordinate |
| `longitude` | Float | Nullable | GPS longitude coordinate |
| `village` | String(100) | Nullable | Village / town name |
| `address` | String(255) | Nullable | Street address |
| `landmark` | String(150) | Nullable | Proximity clue (e.g. Bus Stand) |
| `predicted_category`| String(100) | Not Null | Canonical category output |
| `confidence_score` | Float | Not Null | DistilBERT Softmax score |
| `assigned_department_id` | Integer | FK (`departments.id`) | Dispatched civic department |
| `severity` | String(50) | Not Null | `Critical`, `High`, `Medium`, `Low` |
| `severity_reason` | Text | Nullable | Rule engine explanation |
| `status` | String(50) | Default 'Submitted' | `Submitted`, `Assigned`, `In Progress`, `Resolved`, `Rejected` |
| `resolution_image_path` | String(500) | Nullable | Officer inspection photo |
| `resolution_notes`| Text | Nullable | Work completion notes |
| `created_at` | DateTime | Default UTC | Submission timestamp |
| `updated_at` | DateTime | Auto-update UTC | Modification timestamp |

### 4. `complaint_history`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | History ID |
| `complaint_id` | Integer | FK (`complaints.id`) | Associated complaint |
| `old_status` | String(50) | Nullable | Previous status |
| `new_status` | String(50) | Not Null | Updated status |
| `comment` | Text | Nullable | Administrative notes |
| `updated_by` | Integer | FK (`users.id`) | User who made update |
| `updated_at` | DateTime | Default UTC | Timestamp of update |

### 5. `notifications`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | Notification ID |
| `user_id` | Integer | FK (`users.id`) | Recipient citizen or officer |
| `complaint_id` | Integer | FK (`complaints.id`) | Referenced complaint |
| `message` | Text | Not Null | Alert message |
| `is_read` | Boolean | Default False | Read receipt flag |
| `created_at` | DateTime | Default UTC | Creation timestamp |

### 6. `model_predictions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | Prediction log ID |
| `complaint_id` | Integer | FK (`complaints.id`) | Assigned complaint |
| `predicted_category` | String(100) | Not Null | Output category |
| `confidence` | Float | Not Null | Probability score |
| `model_version` | String(50) | Default 'DistilBERT-v1.0' | Model tag |
| `created_at` | DateTime | Default UTC | Inference timestamp |
