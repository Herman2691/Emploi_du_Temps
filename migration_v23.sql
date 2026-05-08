-- migration_v23.sql
-- Gestion multi-années : un étudiant peut être inscrit dans plusieurs années académiques
-- + marqueur is_recrutement sur les promotions

-- 1. Changer la contrainte unique sur student_registry
--    Ancienne : UNIQUE(student_number, university_id)
--    Nouvelle : UNIQUE(student_number, university_id, annee_academique)
ALTER TABLE student_registry
    DROP CONSTRAINT IF EXISTS student_registry_student_number_university_id_key;

ALTER TABLE student_registry
    ADD CONSTRAINT student_registry_num_uni_annee_key
    UNIQUE(student_number, university_id, annee_academique);

-- 2. Promotion de recrutement (1ère année — liste fraîche chaque année)
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS is_recrutement BOOLEAN DEFAULT FALSE;
