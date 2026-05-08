-- migration_v19.sql
-- Résultats de session calculés : moyennes, rangs et décisions par étudiant

CREATE TABLE IF NOT EXISTS student_session_results (
    id                  SERIAL PRIMARY KEY,
    student_id          INTEGER NOT NULL REFERENCES students(id)  ON DELETE CASCADE,
    class_id            INTEGER NOT NULL REFERENCES classes(id)   ON DELETE CASCADE,
    session_name        VARCHAR(100) NOT NULL,
    academic_year       VARCHAR(9)   NOT NULL,
    average             NUMERIC(5,2),           -- moyenne générale /20
    rank                INTEGER,                -- rang dans la classe
    decision            VARCHAR(20),            -- Admis | Session2 | Ajourné
    threshold_admis     NUMERIC(4,2) DEFAULT 10,
    threshold_session2  NUMERIC(4,2) DEFAULT 7,
    computed_at         TIMESTAMP DEFAULT NOW(),
    computed_by         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(student_id, session_name, academic_year)
);

CREATE INDEX IF NOT EXISTS idx_ssr_class    ON student_session_results(class_id);
CREATE INDEX IF NOT EXISTS idx_ssr_student  ON student_session_results(student_id);
CREATE INDEX IF NOT EXISTS idx_ssr_session  ON student_session_results(session_name);
CREATE INDEX IF NOT EXISTS idx_ssr_decision ON student_session_results(decision);
