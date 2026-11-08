-- 1) Patients + diagnosis + region (multi JOIN)
SELECT p.patient_id_hash, p.sex, p.age, d.icd10, d.icd10_name, r.region_name, o.dt_beg
FROM observation o
JOIN patient p ON p.patient_id_hash = o.patient_id_hash
JOIN diagnosis d ON d.diagnosis_id = o.diagnosis_id
JOIN organization org ON org.organization_id = o.organization_id
JOIN region r ON r.region_id = org.region_id
LIMIT 50;

-- 2) Cases by ICD class with HAVING
SELECT d.icd_class, COUNT(*) AS n_cases
FROM observation o
JOIN diagnosis d ON d.diagnosis_id = o.diagnosis_id
GROUP BY d.icd_class
HAVING COUNT(*) >= 10
ORDER BY n_cases DESC;

-- 3) Top organizations by load
SELECT org.organization_code, r.region_name, COUNT(*) AS n_obs
FROM observation o
JOIN organization org ON org.organization_id = o.organization_id
JOIN region r ON r.region_id = org.region_id
GROUP BY org.organization_code, r.region_name
ORDER BY n_obs DESC
LIMIT 15;

-- 4) Patients with more than one observation (subquery)
SELECT patient_id_hash, cnt
FROM (
    SELECT patient_id_hash, COUNT(*) AS cnt
    FROM observation
    GROUP BY patient_id_hash
) t
WHERE cnt > 1
ORDER BY cnt DESC
LIMIT 20;

-- 5) On registry as of date X (CTE)
WITH params AS (
    SELECT '2023-06-01' AS as_of
),
active AS (
    SELECT o.*
    FROM observation o, params p
    WHERE date(o.dt_beg) <= date(p.as_of)
      AND (o.dt_end IS NULL OR date(o.dt_end) >= date(p.as_of))
)
SELECT d.icd10, COUNT(*) AS on_registry
FROM active a
JOIN diagnosis d ON d.diagnosis_id = a.diagnosis_id
GROUP BY d.icd10
ORDER BY on_registry DESC;

-- 6) Rank regions by case count (window)
SELECT region_name, n_cases,
       RANK() OVER (ORDER BY n_cases DESC) AS region_rank
FROM (
    SELECT r.region_name, COUNT(*) AS n_cases
    FROM observation o
    JOIN organization org ON org.organization_id = o.organization_id
    JOIN region r ON r.region_id = org.region_id
    GROUP BY r.region_name
);

-- 7) Monthly new registrations (CTE)
WITH monthly AS (
    SELECT strftime('%Y-%m', dt_beg) AS ym, COUNT(*) AS new_cases
    FROM observation
    GROUP BY strftime('%Y-%m', dt_beg)
)
SELECT ym, new_cases,
       AVG(new_cases) OVER (
           ORDER BY ym
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ) AS rolling_avg_3m
FROM monthly
ORDER BY ym;

-- 8) Deregistered in period with filters
SELECT d.icd10, p.sex, COUNT(*) AS closed_cases
FROM observation o
JOIN patient p ON p.patient_id_hash = o.patient_id_hash
JOIN diagnosis d ON d.diagnosis_id = o.diagnosis_id
WHERE o.dt_end IS NOT NULL
  AND date(o.dt_end) BETWEEN date('2023-01-01') AND date('2024-12-31')
GROUP BY d.icd10, p.sex
ORDER BY closed_cases DESC;

-- 9) Sex share within region (window)
SELECT region_name, sex, n,
       ROUND(100.0 * n / SUM(n) OVER (PARTITION BY region_name), 2) AS pct_in_region
FROM (
    SELECT r.region_name, p.sex, COUNT(*) AS n
    FROM observation o
    JOIN patient p ON p.patient_id_hash = o.patient_id_hash
    JOIN organization org ON org.organization_id = o.organization_id
    JOIN region r ON r.region_id = org.region_id
    GROUP BY r.region_name, p.sex
)
ORDER BY region_name, sex;

-- 10) Observation duration days (CTE)
WITH dur AS (
    SELECT observation_id,
           CAST(julianday(COALESCE(dt_end, '2024-12-31')) - julianday(dt_beg) AS INT) AS days,
           censored
    FROM observation
)
SELECT censored,
       COUNT(*) AS n,
       ROUND(AVG(days), 1) AS avg_days,
       ROUND(MIN(days), 1) AS min_days,
       ROUND(MAX(days), 1) AS max_days
FROM dur
GROUP BY censored;
