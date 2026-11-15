# Liver Disease Risk Factors and Diagnosis Prediction

**Course:** Programming for Data Analysis and Database  
**Program:** Big Data Analysis (Master)  
**Group:** ADA-2602M  
**Topic:** 38 — Cluster 7 Public Health Open Data Analytics  
**Authors:** Madi Zhakenov, Askhat Aubakirov

## Goal
Estimate how lifestyle and clinical factors relate to liver disease diagnosis and compare Dummy, Logistic Regression, and Random Forest using stratified cross-validation (ROC-AUC, F1, calibration).

## Data (two real layers — no medical synthesis)
1. **Ashyq / Smart Data Ukimet clinical CSV** (~1700 rows)  
   https://ashyq.data.gov.kz/dataset/magda-ds-8ec6e917-d808-494a-b84d-177dd857d7c4/details  
   Columns: Age, Gender, BMI, AlcoholConsumption, Smoking, GeneticRisk, PhysicalActivity, Diabetes, Hypertension, LiverFunctionTest, Diagnosis  
2. **Egov illnesses** filtered to liver ICD-10 (B15–B19, K70–K77, C22) for regional rates  
   https://data.egov.kz/datasets/view?index=illnesses  
3. Population denominators: approximate public regional figures (`stat.gov.kz`)

Instructor guidance: do **not** invent medical registry fields (fake cards, ICD, regions, observation dates).  
Dataset size is below the recommended 500k guideline; that size is **recommended**, not mandatory, and real data without synthesis was agreed.

## Setup
```bash
cd liver_project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m src.main --full
streamlit run src/dashboard_app.py
```

Interactive menu:
```bash
python -m src.main --menu
```

## Pipeline
1. Chunked CSV load, dtype optimization, Parquet export, memory report  
2. Technical `case_id_hash` only (privacy demo) — no fabricated NOMKART  
3. Quality audit + Topic-38 synthetic/engineered heuristic on clinical features  
4. SQLite: `clinical_case` + egov `illness_stat` / `diagnosis` / `region`; 10 SQL queries  
5. EDA on Ashyq; egov ICD volume chart; rates per 100k from egov  
6. Kaplan–Meier skipped (no real observation dates; documented)  
7. Chi-square, Mann–Whitney, odds ratios on clinical factors  
8. Dummy / Logistic Regression / Random Forest with stratified CV  
9. Console menu + Streamlit (clinical filters + egov region/ICD)

## Layout
```
src/       Python modules
db/        schema.sql, queries.sql
data/      raw, interim, processed
reports/   metrics, audits, figures
```

## Contribution
- **Askhat Aubakirov:** data loading, Parquet, privacy, audit, SQLite/SQL  
- **Madi Zhakenov:** EDA, rates, statistical tests, models, Streamlit/CLI  

## Key outputs
After `python -m src.main --full`:
- `reports/memory_report.json`
- `reports/audit_report.json`
- `reports/stat_tests.csv`
- `reports/model_metrics.csv`
- `reports/figures/`
- `reports/sql_result_*.csv`
