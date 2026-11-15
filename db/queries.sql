-- 1) Clinical cases preview (base table)
SELECT case_id_hash, sex, age, age_bin, bmi, alcohol_consumption,
       diabetes, hypertension, liver_function_test, diagnosis_label
FROM clinical_case
ORDER BY age
LIMIT 50;

-- 2) Diagnosis rate by sex with HAVING
SELECT sex,
       COUNT(*) AS n_cases,
       ROUND(AVG(diagnosis_label) * 100.0, 1) AS diagnosis_pct
FROM clinical_case
GROUP BY sex
HAVING COUNT(*) >= 10
ORDER BY diagnosis_pct DESC;

-- 3) Age-bin risk profile (JOIN-free aggregate + filter)
SELECT age_bin,
       COUNT(*) AS n,
       ROUND(AVG(bmi), 1) AS mean_bmi,
       ROUND(AVG(alcohol_consumption), 1) AS mean_alcohol,
       ROUND(AVG(diagnosis_label) * 100.0, 1) AS diagnosis_pct
FROM clinical_case
GROUP BY age_bin
HAVING COUNT(*) >= 10
ORDER BY age_bin;

-- 4) High-risk clinical subset via subquery
SELECT case_id_hash, age, bmi, alcohol_consumption, liver_function_test, diagnosis_label
FROM clinical_case
WHERE alcohol_consumption > (
    SELECT AVG(alcohol_consumption) FROM clinical_case
)
  AND diagnosis_label = 1
ORDER BY alcohol_consumption DESC
LIMIT 30;

-- 5) Egov illness volume by ICD class (JOIN + HAVING)
SELECT d.icd_class,
       COUNT(*) AS n_rows,
       SUM(i.patients_c) AS total_patients
FROM illness_stat i
JOIN diagnosis d ON d.diagnosis_id = i.diagnosis_id
GROUP BY d.icd_class
HAVING SUM(i.patients_c) >= 10
ORDER BY total_patients DESC;

-- 6) Rank regions by egov liver patients (window)
SELECT region_name, total_patients,
       RANK() OVER (ORDER BY total_patients DESC) AS region_rank
FROM (
    SELECT r.region_name, SUM(i.patients_c) AS total_patients
    FROM illness_stat i
    JOIN region r ON r.region_id = i.region_id
    GROUP BY r.region_name
);

-- 7) Rates per 100k by region (CTE + JOIN)
WITH regional AS (
    SELECT r.region_id, r.region_name, r.population,
           SUM(i.patients_c) AS total_patients
    FROM illness_stat i
    JOIN region r ON r.region_id = i.region_id
    GROUP BY r.region_id, r.region_name, r.population
)
SELECT region_name, total_patients, population,
       ROUND(total_patients * 100000.0 / population, 2) AS rate_per_100k
FROM regional
WHERE population > 0 AND total_patients >= 10
ORDER BY rate_per_100k DESC;

-- 8) Top ICD codes within each region (window + CTE)
WITH ranked AS (
    SELECT r.region_name, d.icd10, d.icd10_name,
           SUM(i.patients_c) AS patients,
           ROW_NUMBER() OVER (
               PARTITION BY r.region_name
               ORDER BY SUM(i.patients_c) DESC
           ) AS rn
    FROM illness_stat i
    JOIN region r ON r.region_id = i.region_id
    JOIN diagnosis d ON d.diagnosis_id = i.diagnosis_id
    GROUP BY r.region_name, d.icd10, d.icd10_name
)
SELECT region_name, icd10, icd10_name, patients, rn
FROM ranked
WHERE rn <= 3
ORDER BY region_name, rn;

-- 9) Share of patients by ICD class within region (window)
SELECT region_name, icd_class, patients,
       ROUND(100.0 * patients / SUM(patients) OVER (PARTITION BY region_name), 2) AS pct_in_region
FROM (
    SELECT r.region_name, d.icd_class, SUM(i.patients_c) AS patients
    FROM illness_stat i
    JOIN region r ON r.region_id = i.region_id
    JOIN diagnosis d ON d.diagnosis_id = i.diagnosis_id
    GROUP BY r.region_name, d.icd_class
)
ORDER BY region_name, patients DESC;

-- 10) Clinical vs egov context: national diagnosis share + egov total (CTE)
WITH clinical AS (
    SELECT COUNT(*) AS n_clinical,
           SUM(diagnosis_label) AS n_positive
    FROM clinical_case
),
egov AS (
    SELECT SUM(patients_c) AS n_egov_patients,
           COUNT(DISTINCT region_id) AS n_regions,
           COUNT(DISTINCT diagnosis_id) AS n_icd_codes
    FROM illness_stat
)
SELECT c.n_clinical,
       c.n_positive,
       ROUND(100.0 * c.n_positive / c.n_clinical, 1) AS clinical_positive_pct,
       e.n_egov_patients,
       e.n_regions,
       e.n_icd_codes
FROM clinical c, egov e;
