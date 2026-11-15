# ER diagram (logical) — real Ashyq clinical + egov illnesses

```mermaid
erDiagram
    REGION ||--o{ ILLNESS_STAT : reports
    DIAGNOSIS ||--o{ ILLNESS_STAT : coded_as
    CLINICAL_CASE

    REGION {
        int region_id PK
        string region_name
        int population
    }
    DIAGNOSIS {
        int diagnosis_id PK
        string icd10
        string icd10_name
        string icd_class
    }
    ILLNESS_STAT {
        int stat_id PK
        int region_id FK
        int diagnosis_id FK
        int patients_c
    }
    CLINICAL_CASE {
        string case_id_hash PK
        string sex
        int age
        float bmi
        int diagnosis_label
    }
```

Notes:
- `clinical_case` = Ashyq clinical CSV (no fabricated ICD/region/dates).
- `illness_stat` = real egov open-data aggregates filtered to liver ICD-10.
- No synthetic observation / dispensary / organization medical entities.
