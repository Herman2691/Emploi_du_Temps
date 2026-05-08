-- migration_v21.sql
-- Unités d'Enseignement (UE) et Éléments Constitutifs (EC = cours existants)

CREATE TABLE IF NOT EXISTS unites_enseignement (
    id            SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    code          VARCHAR(30),
    name          VARCHAR(200) NOT NULL,
    credits       NUMERIC(4,1) DEFAULT 0,     -- crédits ECTS de l'UE
    group_label   VARCHAR(10)  DEFAULT 'A',   -- A, B, C ...
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ue_department ON unites_enseignement(department_id);

-- Les cours deviennent des EC (Éléments Constitutifs) d'une UE
ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS ue_id      INTEGER REFERENCES unites_enseignement(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS credits_ec NUMERIC(4,1) DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_courses_ue ON courses(ue_id);

-- Résultats par UE par étudiant (note UE, décision V/NV, crédits obtenus)
CREATE TABLE IF NOT EXISTS student_ue_results (
    id               SERIAL PRIMARY KEY,
    student_id       INTEGER NOT NULL REFERENCES students(id)            ON DELETE CASCADE,
    ue_id            INTEGER NOT NULL REFERENCES unites_enseignement(id) ON DELETE CASCADE,
    session_name     VARCHAR(100) NOT NULL,
    academic_year    VARCHAR(9),
    note_ue          NUMERIC(5,2),
    credits_obtained NUMERIC(4,1) DEFAULT 0,
    decision         VARCHAR(5)   DEFAULT 'NV',  -- V | NV
    computed_at      TIMESTAMP DEFAULT NOW(),
    computed_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(student_id, ue_id, session_name, academic_year)
);

CREATE INDEX IF NOT EXISTS idx_suer_student ON student_ue_results(student_id);
CREATE INDEX IF NOT EXISTS idx_suer_ue      ON student_ue_results(ue_id);
CREATE INDEX IF NOT EXISTS idx_suer_session ON student_ue_results(session_name);
