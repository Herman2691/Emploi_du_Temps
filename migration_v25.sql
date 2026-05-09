-- migration_v25.sql
-- Délibération annuelle (combinaison S1 + S2)

CREATE TABLE IF NOT EXISTS deliberations_annuelles (
    id               SERIAL PRIMARY KEY,
    student_id       INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id         INTEGER NOT NULL REFERENCES classes(id)  ON DELETE CASCADE,
    academic_year    VARCHAR(10) NOT NULL,
    moy_s1           NUMERIC(5,2),
    moy_s2           NUMERIC(5,2),
    moy_annuelle     NUMERIC(5,2),
    credits_obtenus  INTEGER DEFAULT 0,
    credits_total    INTEGER DEFAULT 60,
    ecs_a_reprendre  TEXT,          -- noms séparés par virgule
    decision         VARCHAR(20) DEFAULT 'en_cours', -- admis | redoublant | en_cours
    published        BOOLEAN DEFAULT FALSE,
    published_at     TIMESTAMP,
    published_by     INTEGER REFERENCES users(id),
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, class_id, academic_year)
);

CREATE INDEX IF NOT EXISTS idx_delib_class_year
    ON deliberations_annuelles(class_id, academic_year);
CREATE INDEX IF NOT EXISTS idx_delib_student
    ON deliberations_annuelles(student_id);
