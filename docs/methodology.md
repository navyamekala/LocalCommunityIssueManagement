# Methodology: Local Community Problem Classification Using DistilBERT

## 1. Research Foundation: Kano et al. (2019)

### The Base Paper
- **Title**: *A Method of Extracting and Classifying Local Community Problems from Citizen-Report Data using Text Mining*
- **Authors**: Eiji Kano, Yoshikatsu Fujita, Kazuhiko Tsuda (Procedia Computer Science, Vol. 159, 2019, pp. 1347–1356).
- **Core Finding**: Traditional local government departments categorize complaints based on bureaucratic jurisdiction (e.g., "Roads Department", "Parks Division"). However, citizen problem reports reveal that regional defects objectively fall into seven distinct categories:
  1. **Lamp Breakage**: Streetlight failure, unlit public lanterns, broken fixtures.
  2. **Road Damage**: Potholes, asphalt cracks, subsidence, road collapse.
  3. **Facility Defect**: Damaged benches, playground equipment, boundary walls, public utilities.
  4. **Invisibility**: Obstructions to sightlines, obscured road signs, dirty/broken convex mirrors.
  5. **Overgrowth**: Roadside weeds, overgrown bushes, fallen tree limbs.
  6. **Clogging**: Blocked drainage canals, flooded walkways, culvert obstructions.
  7. **Leaving**: Illegally dumped waste, discarded furniture, abandoned vehicles.

### Comparative Analysis: Base Paper vs. Our Proposed System

| Dimension | Base Paper Methodology (Kano et al., 2019) | Our Proposed System Implementation |
|---|---|---|
| **Text Representation** | Morphological analysis (Mecab), word co-occurrence pairs, dependency trees | Pretrained Subword Tokenization via DistilBERT (`distilbert-base-uncased`) |
| **Classification Engine** | Handcrafted syntactic matching rules & dictionary lookups | Deep Bidirectional Transformer Neural Network fine-tuned end-to-end |
| **Confidence Scoring** | Binary rule matching (No probability distribution) | Softmax class probability distribution + Low-confidence fallback (< 40%) |
| **Severity Scoring** | None (Categories treated without urgency assessment) | Multi-factor rule-based severity scoring (Critical, High, Medium, Low) |
| **Operational Integration** | Offline academic data analysis (No citizen/admin software) | Full-stack interactive web application (FastAPI + React + Leaflet + SQLite) |
| **Citizen Feedback** | None | Real-time GPS location, photo uploads, lifecycle timeline tracking, in-app alerts |

---

## 2. Dataset Pipeline & Preprocessing

- **Dataset Source**: `dataset/local_community_complaints_5000_synthetic-3.csv`
- **Data Nature**: Synthetically generated complaint records mirroring real citizen complaint text structures for safe local development.
- **Preprocessing Steps**:
  1. Null and missing value validation.
  2. Deduplication across `(title, description)` pairs.
  3. Text concatenation: `input_text = f"{title}. {description}"`.
  4. Label encoding across the 7 classes.
  5. Stratified partition:
     - **Training Set (70%)**: Model weight updates via gradient descent.
     - **Validation Set (15%)**: Hyperparameter tuning & early stopping checkpoint selection.
     - **Test Set (15%)**: Strict, independent evaluation with zero data leakage.

---

## 3. DistilBERT Fine-Tuning Pipeline

- **Pretrained Backbone**: `distilbert-base-uncased` (6 transformer layers, 768 hidden dimension, 12 attention heads, 66M parameters).
- **Sequence Length**: 64 tokens (empirically validated to cover >99% of sample token lengths without truncation).
- **Optimization**:
  - Optimizer: `AdamW`
  - Learning Rate: `2e-5`
  - Weight Decay: `0.01`
  - Scheduler: Linear warmup over 10% of total training steps
  - Batch Size: `16`
  - Checkpointing: Best model weights retained based on Validation Macro F1 score.

---

## 4. Severity Assessment Framework

Because the provided dataset does not contain manual severity labels, severity is computed transparently via domain rules rather than fabricated ML predictions:
- **Critical (Score 0.90–0.95)**: Direct public safety hazards (live electric wires, road collapse, sinkholes, water main bursts, or hazardous flooding near schools/hospitals).
- **High (Score 0.75)**: High-disruption infrastructure hazards (large potholes, severe sewage overflow, open manholes, blind curve obstructions).
- **Medium (Score 0.50)**: Standard civic defects (dark streetlights, cracked footpaths, slow drainage, rusted park benches).
- **Low (Score 0.25)**: Routine cosmetic maintenance (minor litter, weed trimming, full trash bins).

---

## 5. Automated Department Routing

Predicted categories map to municipal operational departments:
- `Road Damage` → **Roads Department**
- `Clogging` → **Drainage Department**
- `Lamp Breakage` → **Electrical Department**
- `Facility Defect` → **Public Works Department**
- `Overgrowth` → **Gardening Department**
- `Invisibility` → **Traffic and Safety Department**
- `Leaving` → **Sanitation / Public Area Management**
- `Needs Manual Review` (<40% confidence) → **Public Works / Central Oversight**
