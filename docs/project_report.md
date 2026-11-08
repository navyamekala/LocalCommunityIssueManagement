# Project Report: AI-Based Local Community Issue Reporting and Management System Using DistilBERT

**Author**: Senior Full-Stack Developer & NLP Researcher  
**Framework**: Antigravity Full-Stack Agentic Architecture  
**Academic Context**: Smart Rural Governance & NLP for Civic Infrastructure Management  

---

## Abstract

Rural and semi-urban communities often face significant barriers in reporting and resolving everyday civic problems such as road damages, overflowing drains, streetlight failures, and illegal garbage dumping. Traditional municipal reporting portals rely on complex administrative departmental structures that citizens find confusing, leading to misrouted complaints and prolonged resolution delays. 

This project implements an end-to-end, functional AI-powered web platform called **GramSetu AI** that enables citizens to report local civic issues effortlessly with descriptions, photographs, and GPS geolocation. Using a fine-tuned **DistilBERT** (Bidirectional Encoder Representations from Transformers) deep learning model, the system automatically classifies complaints into seven canonical problem categories identified in the foundational text mining research of **Kano, Fujita, and Tsuda (2019)**. The application assesses problem severity using transparent risk indicators, dispatches issues to dedicated department officers, and facilitates full-lifecycle auditing, interactive map visualization, in-app notifications, and genuine test-set machine learning performance analytics.

---

## 1. Introduction & Motivation

Local governments operate under severe budget and manpower constraints. Simultaneously, citizens in villages and small towns often lack direct channels to report civic deterioration. Existing complaint portals suffer from three major design flaws:
1. **Departmental Silos**: Citizens are forced to guess whether an overflowing culvert belongs to the "Public Works", "Irrigation", or "Drainage" department.
2. **Lack of Severity Prioritization**: High-risk emergencies (e.g., exposed live electrical wires, flash road sinkholes) get queued behind routine cosmetic requests.
3. **Absence of Transparent Tracking**: Citizens receive no structured feedback on their complaints, causing disengagement and loss of civic trust.

**GramSetu AI** bridges this gap by combining modern Transformer Natural Language Processing (NLP) with an intuitive, mobile-friendly interface designed specifically for rural and semi-urban communities.

---

## 2. Research Foundation & Literature Review

### Base Paper Summary
- **Title**: *A Method of Extracting and Classifying Local Community Problems from Citizen-Report Data using Text Mining*
- **Authors**: Eiji Kano, Yoshikatsu Fujita, Kazuhiko Tsuda
- **Publication**: Procedia Computer Science 159 (2019) 1347–1356 (Elsevier B.V.)
- **Key Insight**: The authors investigated the citizen-report mechanism ("Chiba Repo") in Chiba City, Japan. They discovered that classifying problems based on existing bureaucratic departments (e.g., "Roads Division", "Parks Division") masked true problem occurrence patterns. Actual road defects constituted only 16% of total reports. Through morphological analysis and co-occurrence extraction, the researchers established that citizen reports naturally group into **seven distinct problem types**:
  1. **Road Damage**: Physical road surface defects, potholes, cracks, subsidence.
  2. **Clogging**: Blockages in drains, gutters, culverts, and stormwater conduits.
  3. **Lamp Breakage**: Streetlights, public lanterns, and illumination fixture failures.
  4. **Facility Defect**: Broken public benches, fence damages, playground issues.
  5. **Overgrowth**: Roadside weeds, tree branches blocking footpaths.
  6. **Invisibility**: Sightline obstructions, obscured road signs, dirty/broken convex mirrors.
  7. **Leaving**: Illegally abandoned bicycles, dumped household trash, discarded items.

### Research Evolution: From Word Co-occurrence to DistilBERT
While Kano et al. used manual syntactic dependency rules and dictionary matching, our system implements modern **Transformer Deep Learning**:
- Pretrained contextual subword representations (`distilbert-base-uncased`).
- End-to-end fine-tuning on a 5000-sample balanced civic complaint dataset.
- Softmax probability distributions providing true confidence scores.
- Safety fallback ("Needs Manual Review") when confidence drops below 40%.
- Dynamic multi-department routing and rule-based severity rating.

---

## 3. Dataset Characteristics & Preprocessing

The project utilizes `dataset/local_community_complaints_5000_synthetic-3.csv`, a 5,000-row dataset synthetically structured to reflect real citizen report narratives for development purposes.

### Dataset Overview
- **Total Records**: 5,000 complaints
- **Features**: `complaint_id`, `title`, `description`, `category`, `location`, `status`, `source`, `is_real_citizen_report`
- **Missing Values**: 0 missing fields across all columns
- **Class Balance**:
  - `Clogging`: 715 samples (14.3%)
  - `Facility Defect`: 715 samples (14.3%)
  - `Invisibility`: 715 samples (14.3%)
  - `Lamp Breakage`: 715 samples (14.3%)
  - `Overgrowth`: 715 samples (14.3%)
  - `Road Damage`: 715 samples (14.3%)
  - `Leaving`: 710 samples (14.2%)
- **Deduplication**: 3 duplicate `(title, description)` rows were removed, resulting in 4,997 pristine unique samples.
- **Input Text**: Combined representation `f"{title}. {description}"`.
- **Token Length Analysis**: Empirical 99th percentile token length is 52 tokens. A maximum sequence length of 64 tokens captures 100% of information content without truncation while dramatically accelerating training speed.
- **Stratified Partitioning**:
  - **Training Set (70%)**: 3,497 samples
  - **Validation Set (15%)**: 750 samples
  - **Test Set (15%)**: 750 samples

---

## 4. System Architecture & Workflow

### Architectural Modules
1. **Citizen Portal (React + Vite + Leaflet)**:
   - Registration & JWT-secured Login.
   - Problem Reporting with camera capture/upload, HTML5 GPS auto-detection, and Leaflet interactive map pinning.
   - Real-time complaint tracking across 5 lifecycle stages.
   - In-app notification center.

2. **AI NLP Engine (DistilBERT + PyTorch)**:
   - Singleton model loader in memory.
   - Real-time sequence classification.
   - Softmax class probabilities and confidence estimation.
   - Rule-based multi-factor severity engine.

3. **Backend Application Server (FastAPI)**:
   - RESTful API endpoints.
   - Role-Based Access Control (Citizen, Department Admin, Central Superadmin).
   - Relational database management via SQLAlchemy.
   - Audit trail logging every status update with administrator identity and remarks.

4. **Departmental Administration Module**:
   - Filtered complaint queues based on assigned department jurisdiction.
   - Status updates (`Assigned`, `In Progress`, `Resolved`, `Rejected`).
   - Resolution photo upload and verification remarks.

---

## 5. Severity Assessment Engine

The dataset does not contain manual severity labels. In accordance with strict engineering ethics, severity is **not claimed to be learned by the neural network**. Instead, an independent heuristic severity scoring module (`severity.py`) assesses risks based on transparent criteria:
- **Critical (0.90 - 0.95)**: Live electric wires, road collapse, sinkholes, water main bursts, flash flooding near schools/hospitals.
- **High (0.75)**: Large potholes, deep road defects, severe sewage overflow, open manholes, blind curve hazards.
- **Medium (0.50)**: Broken streetlights, cracked footpaths, slow drainage, rusted park benches.
- **Low (0.25)**: Routine weed trimming, small litter, cosmetic maintenance.

---

## 6. Experimental Results & Test Set Evaluation

The DistilBERT model was evaluated on the independent 15% test partition (750 samples) with zero data leakage:
- **Accuracy**: Over 98%
- **Macro F1-Score**: Over 98%
- **Weighted F1-Score**: Over 98%
- **Confusion Matrix**: Demonstrates high diagonal concentration across all seven categories, with balanced precision and recall.
- **Visual Artifacts**:
  - `loss_curve.png`: Convergence of training and validation loss curves.
  - `accuracy_curve.png`: Validation accuracy and macro F1 score progression.
  - `confusion_matrix.png`: Heatmap demonstrating accurate inter-class discrimination.
  - `per_class_metrics.png`: Grouped bar charts comparing precision, recall, and F1 across all categories.

---

## 7. Conclusion & Future Scope

GramSetu AI successfully demonstrates how modern Transformer NLP can bridge the communication gap between citizens and local administrative bodies. By automating the extraction, classification, severity scoring, and routing of community problems, municipal response times can be substantially improved.

**Future Enhancements**:
- Integration with edge mobile apps for offline GPS logging.
- Multilingual speech-to-text allowing citizens to speak complaints in regional languages (e.g., Telugu, Hindi, Tamil).
- Computer Vision model for automated photographic damage severity validation.
