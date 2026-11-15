# Report — Topic 38
**Liver Disease Risk Factors and Diagnosis Prediction**  
Authors: Madi Zhakenov, Askhat Aubakirov | Group ADA-2602M

## 1. Introduction and goal
This project studies associations between lifestyle/clinical factors and liver disease diagnosis and compares three classifiers: Dummy (baseline), Logistic Regression, and Random Forest. Models are evaluated with stratified cross-validation using ROC-AUC, F1, calibration, runtime, and memory.

## 2. Data and sources
Two **real** open-data layers (no fabricated medical registry fields):

| Layer | Source | Role |
|-------|--------|------|
| Clinical risk factors | Ashyq / Smart Data Ukimet liver CSV (~1700 × 11) | EDA, stats, models |
| Regional ICD volume | Egov illnesses filtered to B15–B19, K70–K77, C22 (~1850 rows) | SQL, rates/100k, dashboard region/ICD |
| Population | Approximate public regional figures | Denominators for rates |

Dataset page: https://ashyq.data.gov.kz/dataset/magda-ds-8ec6e917-d808-494a-b84d-177dd857d7c4/details  

**Volume.** The course PDF lists ≥500k rows / 200 MB as a **recommended** size, not a hard mandate. Exceptions are agreed with the instructor. For Topic 38 we keep the official clinical file and do not inflate it with synthetic patients (instructor guidance).

## 3. Preprocessing and privacy
- Chunked CSV load, dtype downcast, Parquet export (`memory_report.json`)
- Technical `case_id_hash` (salted SHA-256) used only as a DB key — Ashyq has no native NOMKART
- Salt stays in local `.env`; raw keys are not committed
- Groups with fewer than 10 observations are suppressed in egov regional tables

## 4. Database and SQL
- Normalized SQLite: `clinical_case`, `region`, `diagnosis`, `illness_stat`
- ER: `db/er_diagram.md`
- Ten SQL queries with JOIN, GROUP BY/HAVING, subquery, CTE, and window functions (`db/queries.sql`)

## 5. EDA, rates, survival
- Clinical figures: class balance, risk boxplots, correlation heatmap
- Egov ICD volume chart (real aggregates; no invented monthly registry calendar)
- Regional rates per 100k from egov illnesses (`illnesses_liver_rates_per_100k.csv`)
- **Kaplan–Meier:** not computed — Ashyq has no DT_BEG/DT_END/censoring; we do not synthesize follow-up spells (`survival_summary.csv`)

## 6. Statistical tests
- Chi-square for binary factors; Mann–Whitney for continuous factors (`stat_tests.csv`)
- Logistic odds ratios with confidence intervals (`logistic_odds_ratios.csv`)

## 7. Models (stratified 5-fold CV, Ashyq clinical features only)

| Model | ROC-AUC | F1 | Seconds | Peak memory (MB) |
|-------|--------:|---:|--------:|-----------------:|
| Dummy | 0.5000 | 0.7102 | 0.24 | 0.61 |
| Logistic Regression | 0.8968 | 0.8286 | 0.29 | 0.64 |
| Random Forest | 0.9439 | 0.9100 | 20.86 | 1.60 |

- Calibration: `figures/07_calibration.png`
- Coefficients: `logreg_coefficients.csv`

## 8. Limitations
1. Ashyq clinical file is small relative to the recommended volume guideline; instructor agreed to use real data without synthesis.
2. Ashyq has no native registry attributes (card id, ICD-10, region, observation dates). Those are **not invented**. Regional ICD analyses use real egov illnesses instead.
3. Distribution checks may still flag Ashyq clinical features as engineered/synthetic — reported in the audit.
4. Without observation dates, Kaplan–Meier vs naive duration cannot be estimated honestly.
5. Regional population values are approximate.

## 9. Conclusions
Clinical features separate diagnosis classes substantially above the Dummy baseline. Logistic Regression provides interpretable odds ratios; Random Forest improves discrimination at higher computational cost. Public-health context (rates, ICD volume) is grounded in egov open data rather than fabricated patient spells. Pipeline: `python -m src.main --full`.

## 10. Contribution
- Askhat Aubakirov: data IO, privacy, audit, database and SQL  
- Madi Zhakenov: EDA, rates, statistics, modeling, interfaces  

## References
- Smart Data Ukimet / Ashyq Data — Liver disease data  
- https://data.egov.kz/datasets/view?index=illnesses  
- https://stat.gov.kz  
- scikit-learn; SciPy; statsmodels  
