-- ============================================================
-- MIGRATION V2 — Comptes Professeurs, Étudiants, TPs, Notes
-- À exécuter dans Supabase SQL Editor (après schema.sql)
-- ============================================================

-- 1. Ajouter le rôle 'professeur' dans la table users
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('super_admin','admin_universite','admin_faculte',
                    'admin_departement','professeur'));

-- Lier users.professor_id → professors.id
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    professor_id INTEGER REFERENCES professors(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_users_professor ON users(professor_id);

-- ============================================================
-- 2. Registre officiel des étudiants (liste importée par l'admin)
-- ============================================================
CREATE TABLE IF NOT EXISTS student_registry (
    id              SERIAL PRIMARY KEY,
    student_number  VARCHAR(50) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    university_id   INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    class_id        INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    is_registered   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_number, university_id)
);
CREATE INDEX IF NOT EXISTS idx_registry_uni   ON student_registry(university_id);
CREATE INDEX IF NOT EXISTS idx_registry_class ON student_registry(class_id);

-- ============================================================
-- 3. Comptes étudiants
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    id              SERIAL PRIMARY KEY,
    student_number  VARCHAR(50) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    email           VARCHAR(255),
    password_hash   TEXT NOT NULL,
    class_id        INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    university_id   INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    registry_id     INTEGER REFERENCES student_registry(id),
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_number, university_id)
);
CREATE INDEX IF NOT EXISTS idx_students_class  ON students(class_id);
CREATE INDEX IF NOT EXISTS idx_students_uni    ON students(university_id);
CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number);

-- ============================================================
-- 4. Documents de cours (PDFs uploadés par les profs)
-- ============================================================
CREATE TABLE IF NOT EXISTS course_documents (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    professor_id    INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    file_url        TEXT NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_size_kb    INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_course_docs_course ON course_documents(course_id);
CREATE INDEX IF NOT EXISTS idx_course_docs_prof   ON course_documents(professor_id);

-- ============================================================
-- 5. Devoirs / Travaux Pratiques
-- ============================================================
CREATE TABLE IF NOT EXISTS tp_assignments (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    professor_id    INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    class_id        INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    deadline        TIMESTAMP NOT NULL,
    is_open         BOOLEAN DEFAULT TRUE,
    max_file_mb     INTEGER DEFAULT 10,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tp_class  ON tp_assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_tp_prof   ON tp_assignments(professor_id);
CREATE INDEX IF NOT EXISTS idx_tp_course ON tp_assignments(course_id);

-- ============================================================
-- 6. Soumissions des TPs par les étudiants
-- ============================================================
CREATE TABLE IF NOT EXISTS tp_submissions (
    id                  SERIAL PRIMARY KEY,
    tp_assignment_id    INTEGER NOT NULL REFERENCES tp_assignments(id) ON DELETE CASCADE,
    student_id          INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    file_url            TEXT NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    file_size_kb        INTEGER DEFAULT 0,
    submitted_at        TIMESTAMP DEFAULT NOW(),
    grade               FLOAT,
    grade_comment       TEXT,
    graded_at           TIMESTAMP,
    UNIQUE(tp_assignment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_submissions_tp      ON tp_submissions(tp_assignment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON tp_submissions(student_id);

-- ============================================================
-- 7. Notes publiées par les professeurs
-- ============================================================
CREATE TABLE IF NOT EXISTS grades (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    professor_id    INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    grade           FLOAT NOT NULL CHECK (grade >= 0),
    max_grade       FLOAT NOT NULL DEFAULT 20.0,
    exam_type       VARCHAR(50) NOT NULL DEFAULT 'Examen',
    comment         TEXT,
    published_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, course_id, exam_type)
);
CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_course  ON grades(course_id);

-- ============================================================
-- Triggers updated_at pour nouvelles tables
-- ============================================================
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['students', 'tp_assignments']
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            JOIN pg_class ON pg_class.oid = pg_trigger.tgrelid
            WHERE pg_trigger.tgname = 'trg_' || t || '_updated'
              AND pg_class.relname = t
        ) THEN
            EXECUTE format('
                CREATE TRIGGER trg_%s_updated
                BEFORE UPDATE ON %s
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            ', t, t);
        END IF;
    END LOOP;
END;
$$;

-- ============================================================
-- SUPABASE STORAGE — À créer manuellement dans le dashboard
-- ============================================================
-- 1. Créer un bucket public nommé : course-docs
-- 2. Créer un bucket public nommé : tp-submissions
-- (Storage > New bucket > cocher "Public bucket")
