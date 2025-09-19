# NeuralDAO-Sub-final  
# DocPilot  

Full-stack, patient-aware intelligence that turns messy clinical data into instant, query-ready signal—then renders it live on a dynamic UI with edit-in-place control. Ingest. Filter. Generate. Visualize. Ship.

---

## 🌟 Key Features

- **LLM-Powered Query Interpretation** — Translate natural language into precise, patient-centric filters with surgical accuracy. Real questions, real answers, zero fluff.  
- **FHIR CSV Integration** — Standardized clinical data as CSVs with schema discipline, perfect for blazing-fast analytics and cloud workflows.  
- **Dynamic Tables** — Auto-generate tables from JSON/CSV with real-time updates—no static dashboards, only live intel.  
- **Edit/Remove Functionality** — One-click edits that sync back to source files and reflect instantly in the UI.  
- **Patient Data Processing** — Clean, segregate, merge, and structure clinical records at scale for rocket-fast downstream ops.  
- **Database Generation** — Per-patient SQL tables for sub-second queries and effortless cohort slicing.  
- **Cloud Storage Upload** — One command to push merged datasets to Supabase buckets—global, portable, and linkable.  
- **Performance Testing** — DuckDB-powered stress tests that prove throughput at league speed.  

---

## 📝 Topics Covered

1. **LLM Usage** — From “human ask” to “machine execution” in one pass.  
2. **FHIR CSV Handling** — Normalize, prefix, and merge multi-source clinical data into clean, queryable artifacts.  
3. **Dynamic UI Generation** — Data-driven tables with instant render and action controls.  
4. **Supabase Integration** — Cloud-native distribution for merged patient datasets.  
5. **Clinical Analysis** — Lightspeed queries across vitals, meds, procedures, observations.  
6. **Database Management** — SQL-first design for explainable, reproducible answers.  
7. **Performance Metrics** — DuckDB benchmarks that keep it honest at scale.  

---

## ⚡ Step-by-Step Workflow

### 1️⃣ CSV Data Processing  
- Clean Individual Files — Prefix columns by source (allergies_NAME, meds_NAME, obs_NAME) for conflict-free merges.  
- Segregate per Patient — Isolate records by patient into dedicated folders for surgical control.  
- Merge Files — Emit merged_patient_data.csv per patient—single source of truth that’s analytics-ready.  
- Clean Temp Files — Keep only what ships; artifacts stay lean and lethal.  

### 2️⃣ SQL / Database Generation  
- Create one table per patient from merged CSVs for ultra-targeted queries and privacy boundaries.  
- Insert records in bulk; storage-agnostic: SQLite, DuckDB, Supabase, or any SQL sink.  

### 3️⃣ Supabase Upload  
- Auto-upload merged CSVs with bucket paths: patient_{id}/merged_patient_data.csv and return shareable links.  

### 4️⃣ DuckDB Stress Testing  
- Multi-query gauntlet per patient: demographics, record density, expense/procedure rollups—with latency, pass/fail, and verdict.  
- Verdict tiers:
  - Excellent: >95% success rate & fast queries.  
  - Good: 85–95% success rate.  
  - Needs work: <85% success rate.  

### 5️⃣ Frontend Interaction  
- Input: “Show patients older than 70 with high BP.” The LLM compiles intent → backend filters CSV/DB → UI renders tables live with edit/remove.  

---

## 🖥 Code Overview

### Backend Highlights
| File                      | Purpose                                                     |
|---------------------------|-------------------------------------------------------------|
| `app.py`                  | API surface for query → result, file ops, and orchestration.|
| `model.py`                | Decision layer for query interpretation and route selection.|
| `patient_data_processing.py` | Clean, segregate, merge, and emit per-patient SQL tables.  |
| `supabase_upload.py`      | Push merged CSVs to Supabase and mint URLs.                 |
| `duckdb_stress_test.py`   | Fire-and-measure performance runs across all patients.      |

### Frontend Highlights
| File                      | Purpose                                                    |
|---------------------------|------------------------------------------------------------|
| `index.html`              | Landing surface for query input + result tables.           |
| `style.css`               | Clean, responsive layout tuned for dense clinical data.    |
| `script.js`               | API calls, smart rendering, and action wiring.             |

---

## 📂 Folder Structure

NeuralDAO-Sub-final/
├─ backend/ # Core logic, CSV processing, uploads, performance tests.
├─ frontend/ # Dynamic UI: HTML/CSS/JS.
├─ data/ # Patient CSVs (FHIR-aligned).
└─ README.md # You are here.


---

## 🔑 Key Observations & Conclusions

- **Automated Patient Processing** — From chaos to a single merged CSV per patient for instant querying.  
- **Supabase Integration** — One push to global storage for collaboration and pipelines.  
- **DuckDB Stress Test** — Performance receipts, not promises.  
- **Patient-Centric Database** — Per-patient tables make privacy-aware analytics simple and fast.  
- **Frontend-Backend Harmony** — UI edits sync back to sources and roundtrip through the API.  

---

## 🛠 Setup & Run

### Prerequisites
- Python 3.x, Node.js & npm (optional).  
- Libraries: pandas, duckdb, supabase, flask, tensorflow/torch (optional).  
- Supabase project + storage bucket.

### Steps

1) Clone Repo  
```
git clone https://github.com/Havish06/NeuralDAO-Sub-final.git
cd NeuralDAO-Sub-final
```
2) Backend
```
cd backend
pip install -r requirements.txt
python app.py
```
3) Frontend  
- Open `frontend/index.html` directly, or run with a dev server.

4) Patient CSV Processing
```
from patient_data_processing import *
create_master_patient_database('data/patients')
```

---

## 📌 Next Steps

- Real-time SQL/NoSQL mode for streaming updates.  
- Trend visualizations for labs/vitals with chart overlays.  
- Role-based access control for clinical-grade governance.  
- Smarter query engine with richer selectors and scoring.  

---

DocPilot transforms clinical chaos into clarity — fast, reliable, scalable, and auditable.

---
