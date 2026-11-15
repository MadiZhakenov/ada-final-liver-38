PRAGMA foreign_keys = OFF;

-- Drop legacy synthetic-registry tables and current schema.
DROP TABLE IF EXISTS observation;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS organization;
DROP TABLE IF EXISTS dispensary_group;
DROP TABLE IF EXISTS illness_stat;
DROP TABLE IF EXISTS clinical_case;
DROP TABLE IF EXISTS diagnosis;
DROP TABLE IF EXISTS region;

PRAGMA foreign_keys = ON;

CREATE TABLE region (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE,
    population INTEGER NOT NULL
);

CREATE TABLE diagnosis (
    diagnosis_id INTEGER PRIMARY KEY,
    icd10 TEXT NOT NULL UNIQUE,
    icd10_name TEXT NOT NULL,
    icd_class TEXT NOT NULL
);

-- Real Ashyq clinical risk-factor rows (no fabricated registry fields).
CREATE TABLE clinical_case (
    case_id_hash TEXT PRIMARY KEY,
    sex TEXT NOT NULL,
    age INTEGER NOT NULL,
    age_bin TEXT,
    bmi REAL,
    alcohol_consumption REAL,
    smoking INTEGER,
    genetic_risk INTEGER,
    physical_activity REAL,
    diabetes INTEGER,
    hypertension INTEGER,
    liver_function_test REAL,
    diagnosis_label INTEGER NOT NULL
);

-- Real egov illnesses aggregates filtered to liver ICD-10 codes.
CREATE TABLE illness_stat (
    stat_id INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES region(region_id),
    diagnosis_id INTEGER NOT NULL REFERENCES diagnosis(diagnosis_id),
    patients_c INTEGER NOT NULL,
    cat TEXT,
    code TEXT,
    subcode TEXT,
    sdu_load_i REAL
);

CREATE INDEX idx_case_sex ON clinical_case(sex);
CREATE INDEX idx_case_diag ON clinical_case(diagnosis_label);
CREATE INDEX idx_ill_region ON illness_stat(region_id);
CREATE INDEX idx_ill_diag ON illness_stat(diagnosis_id);
