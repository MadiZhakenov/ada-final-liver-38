# Report — Topic 38
**Liver Disease Risk Factors and Diagnosis Prediction**  
Authors: Madi Zhakenov, Askhat Aubakirov | Group ADA-2602M

## 1. Introduction and goal
This project studies associations between lifestyle/clinical factors and liver disease diagnosis and compares three classifiers: Dummy (baseline), Logistic Regression, and Random Forest. Models are evaluated with stratified cross-validation using ROC-AUC, F1, calibration, runtime, and memory.

## 2. Data and sources
- Ashyq / Smart Data Ukimet liver dataset: https://ashyq.data.gov.kz/dataset/magda-ds-8ec6e917-d808-494a-b84d-177dd857d7c4/details
- File size in use: 1,700 rows × 11 clinical columns
- Target: Diagnosis (0/1), positive share ≈ 55%
- Regional population denominators for per-100k rates are approximate public figures

## 3. Preprocessing and privacy
- Chunked CSV load, dtype downcast, Parquet export
- Memory reduced from about 0.143 MB to 0.037 MB (`memory_report.json`)
- Patient identifiers are hashed with salted SHA-256 before SQLite; salt is kept in local `.env` only
- Groups with fewer than 10 observations are suppressed in regional tables

## 4. Database and SQL
- Normalized SQLite schema: patient, diagnosis, region, organization, dispensary_group, observation
- ER description: `db/er_diagram.md`
- Ten SQL queries covering JOIN, GROUP BY/HAVING, subquery, CTE, and window functions (`db/queries.sql`)

## 5. EDA, time series, survival, rates
- Figures in `reports/figures/`
- Naive mean observation duration ≈ 436 days; Kaplan–Meier median ≈ 460 days; 425/1700 censored (`survival_summary.csv`)
- Regional rates per 100k: `rates_per_100k.csv`

## 6. Statistical tests
- Chi-square for binary factors; Mann–Whitney for continuous factors (`stat_tests.csv`)
- Logistic odds ratios with confidence intervals (`logistic_odds_ratios.csv`)

## 7. Models (stratified 5-fold CV)

| Model | ROC-AUC | F1 | Seconds | Peak memory (MB) |
|-------|--------:|---:|--------:|-----------------:|
| Dummy | 0.5000 | 0.7102 | 0.08 | 0.61 |
| Logistic Regression | 0.8968 | 0.8286 | 0.11 | 0.64 |
| Random Forest | 0.9439 | 0.9100 | 8.18 | 1.58 |

- Calibration: `figures/07_calibration.png`
- Coefficients: `logreg_coefficients.csv`

## 8. Limitations
1. The published clinical CSV is comparatively small relative to the course volume guideline.
2. The source file has no native registry fields (card id, ICD-10, region, observation dates). Those attributes are constructed in preprocessing to support Cluster 7 SQL, survival, and dashboard requirements and are not presented as original Ukimet registry columns.
3. Distribution checks indicate limited natural correlation structure; this is reported in the audit output.
4. Regional population values are approximate.

## 9. Conclusions
Clinical features separate diagnosis classes substantially above the Dummy baseline. Logistic Regression provides interpretable odds ratios (ROC-AUC ≈ 0.90); Random Forest improves discrimination (ROC-AUC ≈ 0.94) at higher computational cost. The full analysis pipeline is reproducible via `python -m src.main --full`.

## 10. Contribution
- Askhat Aubakirov: data IO, privacy, audit, database and SQL  
- Madi Zhakenov: EDA, survival, rates, statistics, modeling, interfaces  

## References
- Smart Data Ukimet / Ashyq Data — Liver disease data  
- https://stat.gov.kz  
- scikit-learn; lifelines  
