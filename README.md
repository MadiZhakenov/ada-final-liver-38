# Liver Disease Risk Factors and Diagnosis Prediction

**Course:** Programming for Data Analysis and Database  
**Program:** Big Data Analysis (Master)  
**Group:** ADA-2602M  
**Topic:** 38 — Cluster 7 Public Health Open Data Analytics  
**Authors:** Madi Zhakenov, Askhat Aubakirov

## Goal
Estimate how lifestyle and clinical factors relate to liver disease diagnosis and compare Dummy, Logistic Regression, and Random Forest using stratified cross-validation (ROC-AUC, F1, calibration).

## Data
- Dataset page: https://ashyq.data.gov.kz/dataset/magda-ds-8ec6e917-d808-494a-b84d-177dd857d7c4/details
- File: https://s3.sdu.gov.kz/magda-datasets/Liver_disease_data.csv
- Columns: Age, Gender, BMI, AlcoholConsumption, Smoking, GeneticRisk, PhysicalActivity, Diabetes, Hypertension, LiverFunctionTest, Diagnosis
- Population denominators for regional rates: approximate values aligned with public regional statistics (`stat.gov.kz`)

The source file contains clinical risk factors only. Registry-oriented attributes required by Cluster 7 (hashed patient id, ICD-10, region, organization, observation dates, censoring) are added in a controlled preprocessing step and described in the report limitations. Raw identifiers are never stored in the database or repository.

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
2. Salted hashing of patient identifiers before database load  
3. Data-quality audit and distribution checks  
4. SQLite schema and SQL queries (JOIN, HAVING, subquery, CTE, window functions)  
5. EDA, monthly registry series, Kaplan–Meier vs naive duration, rates per 100k  
6. Chi-square, Mann–Whitney, odds ratios  
7. Dummy / Logistic Regression / Random Forest with stratified CV  
8. Console menu and Streamlit dashboard (region, ICD class, sex, period)

## Layout
```
src/       Python modules
db/        schema.sql, queries.sql
data/      raw, interim, processed
reports/   metrics, audits, figures
```

## Contribution
- **Askhat Aubakirov:** data loading, Parquet, privacy, audit, SQLite/SQL  
- **Madi Zhakenov:** EDA, survival, rates, statistical tests, models, Streamlit/CLI  

## Key outputs
After `python -m src.main --full`:
- `reports/memory_report.json`
- `reports/audit_report.json`
- `reports/stat_tests.csv`
- `reports/model_metrics.csv`
- `reports/figures/`
- `reports/sql_result_*.csv`
