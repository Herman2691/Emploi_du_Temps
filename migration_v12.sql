-- migration_v12.sql
-- Point 5  : prévention des doublons de notes (contrainte unique)
-- Point 12 : validation des réponses aux réclamations par le département

-- Point 5 : contrainte unique pour éviter deux notes identiques (même étudiant,
--            même cours, même type, même session)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'grades_no_duplicate'
          AND conrelid = 'grades'::regclass
    ) THEN
        ALTER TABLE grades
            ADD CONSTRAINT grades_no_duplicate
                UNIQUE (student_id, course_id, exam_type, session_name);
    END IF;
END $$;

-- Point 12 : colonnes pour la validation département des réponses aux réclamations
ALTER TABLE grade_claims
    ADD COLUMN IF NOT EXISTS dept_validated    BOOLEAN   DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS dept_validated_by INTEGER   REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS dept_validated_at TIMESTAMP DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS dept_notes        TEXT      DEFAULT NULL;
