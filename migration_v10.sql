-- ============================================================
-- MIGRATION V10 — Sessions d'examens + publication par session
-- ============================================================

-- Ajouter session_name et is_published à grades
ALTER TABLE grades
    ADD COLUMN IF NOT EXISTS session_name VARCHAR(100) NOT NULL DEFAULT 'Principale',
    ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT FALSE;

-- Supprimer l'ancienne contrainte unique (student, course, exam_type)
ALTER TABLE grades
    DROP CONSTRAINT IF EXISTS grades_student_id_course_id_exam_type_key;

-- Nouvelle contrainte unique incluant session_name
ALTER TABLE grades
    ADD CONSTRAINT grades_student_id_course_id_exam_type_session_key
    UNIQUE (student_id, course_id, exam_type, session_name);

-- Index pour les requêtes par session et par publication
CREATE INDEX IF NOT EXISTS idx_grades_session   ON grades(session_name);
CREATE INDEX IF NOT EXISTS idx_grades_published ON grades(is_published);
