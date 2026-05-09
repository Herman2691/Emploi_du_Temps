-- migration_v8.sql
-- Ajout du sujet PDF pour les TPs

ALTER TABLE tp_assignments
    ADD COLUMN IF NOT EXISTS subject_url       TEXT,
    ADD COLUMN IF NOT EXISTS subject_file_name VARCHAR(255);
