# NeuralDAO-Sub-final
# DocPilot

This repository demonstrates a *full-stack patient query system* integrating:
- *Patient-Centric FHIR CSVs*
- *LLM-powered query interpretation*
- *Dynamic UI for data visualization*
- *Automated backend processing, database generation, and cloud storage*

---

## 🌟 Key Features

- *LLM-Powered Query Interpretation* – Parse user input semantically to identify conditions.  
- *FHIR CSV Integration* – Patient data stored in .csv files with standardized column names.  
- *Dynamic Tables* – Frontend tables generated from JSON/CSV dynamically.  
- *Edit/Remove Functionality* – Directly updates backend CSVs.  
- *Patient Data Processing* – Clean, segregate, merge, and structure patient data for analysis.  
- *Database Generation* – SQL tables per patient for easy querying.  
- *Cloud Storage Upload* – Automated upload to *Supabase Storage*.  
- *Performance Testing* – Stress test patient queries using *DuckDB*.

---

## 📝 Topics Covered

1. *LLM Usage* – Understanding complex queries.  
2. *FHIR CSV Handling* – Cleaning, merging, and structuring clinical data.  
3. *Dynamic UI Generation* – Tables with edit/remove for patient-centric info.  
4. *Supabase Integration* – Centralized cloud storage for merged patient CSVs.  
5. *Clinical Analysis* – Queries on BP, sugar, vitals, medications, procedures.  
6. *Database Management* – SQL generation and execution per patient.  
7. *Performance Metrics* – DuckDB stress testing for all patients.

---

## ⚡ Step-by-Step Workflow

### 1️⃣ CSV Data Processing

1. *Clean Individual Files* – Prefix columns with source name (allergies_NAME, etc.).  
2. *Segregate per Patient* – Create individual folders per patient.  
3. *Merge Files* – Produce merged_patient_data.csv per patient.  
4. *Clean Temp Files* – Keep only merged CSVs.  

### 2️⃣ SQL / Database Generation

- Generate *one table per patient* using merged CSVs.
- Insert all records for easy querying.
- Optionally store in *SQLite, **Supabase*, or any SQL database.

### 3️⃣ Supabase Upload

- Automates upload of merged CSVs to Supabase Storage.  
- Bucket structure: patient_{id}/merged_patient_data.csv.  
- Generates *public URLs* for each patient file.

### 4️⃣ DuckDB Stress Testing

- Runs multiple queries per patient:
  - Patient demographics
  - Clinical record counts
  - Healthcare summary (expenses & procedures)  
- Tracks *query execution time, **success/failure*, and performance metrics.  
- Provides a *performance verdict*:
  - Excellent: >95% success rate & fast queries  
  - Good: 85–95% success rate  
  - Needs work: <85% success rate  

### 5️⃣ Frontend Interaction

- User inputs query: "Show patients older than 70 with high BP."  
- LLM interprets query → backend filters CSV/DB → frontend dynamically renders table.  
- Supports *edit/remove* functionality directly updating CSV.  

---

## 🖥 Code Overview

### Backend Highlights

| File | Purpose |
|------|---------|
| app.py | Main server exposing API endpoints. |
| model.py | Neural network model logic for DAO decisions. |
| patient_data_processing.py | Clean, segregate, merge patient CSVs, generate SQL tables. |
| supabase_upload.py | Upload merged CSVs to Supabase Storage, generate URLs. |
| duckdb_stress_test.py | Test query performance on all patient CSVs. |

### Frontend Highlights

| File | Purpose |
|------|---------|
| index.html | User input form and dynamic table container. |
| style.css | UI design & responsiveness. |
| script.js | Sends API requests and renders dynamic tables. |

---

## 📂 Folder Structure


NeuralDAO-Sub-final/
├─ backend/            # Python scripts (NeuralDAO logic, CSV processing, Supabase upload, DuckDB testing)
├─ frontend/           # HTML, CSS, JS for dynamic UI
├─ data/               # FHIR CSV patient files
└─ README.md


---

## 🔑 Key Observations & Conclusions

- *Automated Patient Processing* – Each patient is processed into a single merged CSV → easier querying.  
- *Supabase Integration* – Centralized cloud storage for large datasets.  
- *DuckDB Stress Test* – Confirms query speed, success rate, and highlights errors for optimization.    
- *Patient-Centric Database* – Each patient has a separate SQL table → simplifies analytics and compliance.  
- *Frontend-Backend Harmony* – Dynamic table updates are synced with backend changes seamlessly.

---

## 🛠 Setup & Run

### Prerequisites

- Python 3.x  
- Node.js & npm (if using frameworks)  
- Libraries: pandas, duckdb, supabase, flask, tensorflow/torch (if needed)  
- Supabase account & bucket setup  

### Steps

1. *Clone Repo*

bash
git clone https://github.com/Havish06/NeuralDAO-Sub-final.git
cd NeuralDAO-Sub-final


2. *Backend*

bash
cd backend
pip install -r requirements.txt
python app.py


3. *Frontend*

- Open frontend/index.html or use dev server for dynamic JS features.

4. *Patient CSV Processing*

python
from patient_data_processing import *
create_master_patient_database('data/patients')


5. *Supabase Upload*

python
from supabase_upload import upload_all_patients_to_supabase
upload_all_patients_to_supabase('data/patients')


6. *DuckDB Stress Test*

python
from duckdb_stress_test import stress_test_all_patients_real_columns
stress_test_all_patients_real_columns('data/patients')


---

## 📌 Next Steps

- Integrate *real-time SQL/NoSQL database* instead of CSV.  
- Visualize lab results & vitals trends with charts.  
- Add *role-based access control* for patient data.  
- Expand NeuralDAO logic for more sophisticated decision-making.
