PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS observation;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS diagnosis;
DROP TABLE IF EXISTS region;
DROP TABLE IF EXISTS organization;
DROP TABLE IF EXISTS dispensary_group;

CREATE TABLE region (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE,
    population INTEGER NOT NULL
);

CREATE TABLE organization (
    organization_id INTEGER PRIMARY KEY,
    organization_code TEXT NOT NULL UNIQUE,
    region_id INTEGER NOT NULL REFERENCES region(region_id)
);

CREATE TABLE diagnosis (
    diagnosis_id INTEGER PRIMARY KEY,
    icd10 TEXT NOT NULL UNIQUE,
    icd10_name TEXT NOT NULL,
    icd_class TEXT NOT NULL
);

CREATE TABLE dispensary_group (
    group_id INTEGER PRIMARY KEY,
    group_code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE patient (
    patient_id_hash TEXT PRIMARY KEY,
    sex TEXT NOT NULL,
    age INTEGER NOT NULL,
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

CREATE TABLE observation (
    observation_id INTEGER PRIMARY KEY,
    patient_id_hash TEXT NOT NULL REFERENCES patient(patient_id_hash),
    diagnosis_id INTEGER NOT NULL REFERENCES diagnosis(diagnosis_id),
    organization_id INTEGER NOT NULL REFERENCES organization(organization_id),
    group_id INTEGER NOT NULL REFERENCES dispensary_group(group_id),
    dt_beg TEXT NOT NULL,
    dt_end TEXT,
    censored INTEGER NOT NULL
);

CREATE INDEX idx_obs_patient ON observation(patient_id_hash);
CREATE INDEX idx_obs_diag ON observation(diagnosis_id);
CREATE INDEX idx_obs_beg ON observation(dt_beg);
