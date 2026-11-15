# Presentation outline

1. Title — Topic 38 Liver Disease Risk and Diagnosis Prediction | Zhakenov, Aubakirov | ADA-2602M  
2. Problem and goal  
3. Data: two real layers (Ashyq clinical + egov liver ICD) — no medical synthesis  
4. Volume note: 500k is recommended; instructor agreed real small file  
5. Pipeline overview (chunks → Parquet → audit → SQLite → EDA/models)  
6. Privacy: technical case_id_hash only (no fabricated NOMKART)  
7. Quality audit + engineered-feature check  
8. Database schema and SQL examples (clinical + egov)  
9. EDA + egov rates per 100k  
10. Why KM skipped (no observation dates; no fake spells)  
11. Statistical tests and odds ratios  
12. Model comparison (Dummy / LogReg / RF)  
13. Dashboard demo (clinical tab + egov region/ICD tab)  
14. Limitations + conclusions + contribution  

Demo: `python -m src.main --menu` and `streamlit run src/dashboard_app.py`
