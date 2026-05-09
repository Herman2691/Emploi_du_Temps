-- migration_v15.sql
-- Ajout : Filières, Options d'étude, Inscriptions académiques,
--         Présences, Messages classe, Réclamations de notes

-- ─── 1. FILIÈRES (sous les départements) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS filieres (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    code          VARCHAR(20),
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    description   TEXT    DEFAULT '',
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_filieres_dept ON filieres(department_id);

-- ─── 2. OPTIONS D'ÉTUDE (sous les filières) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS options_etude (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    code        VARCHAR(20),
    filiere_id  INTEGER NOT NULL REFERENCES filieres(id) ON DELETE CASCADE,
    description TEXT    DEFAULT '',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_options_filiere ON options_etude(filiere_id);

-- ─── 3. RATTACHEMENT OPTIONNEL DES PROMOTIONS AUX FILIÈRES/OPTIONS ───────────
ALTER TABLE promotions ADD COLUMN IF NOT EXISTS filiere_id INTEGER REFERENCES filieres(id);
ALTER TABLE promotions ADD COLUMN IF NOT EXISTS option_id  INTEGER REFERENCES options_etude(id);

-- ─── 4. INSCRIPTIONS ACADÉMIQUES (suivi de progression étudiant) ──────────────
CREATE TABLE IF NOT EXISTS academic_enrollments (
    id            SERIAL PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students(id)   ON DELETE CASCADE,
    class_id      INTEGER NOT NULL REFERENCES classes(id),
    promotion_id  INTEGER NOT NULL REFERENCES promotions(id),
    option_id     INTEGER          REFERENCES options_etude(id),
    academic_year VARCHAR(9)  NOT NULL,   -- ex : "2024-2025"
    status        VARCHAR(20) DEFAULT 'inscrit',
    -- inscrit | admis | redoublant | transfere | abandonne
    enrolled_at   TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW(),
    changed_by    INTEGER   REFERENCES users(id),
    notes         TEXT,
    UNIQUE(student_id, academic_year)
);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON academic_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_class   ON academic_enrollments(class_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_year    ON academic_enrollments(academic_year);

-- ─── 5. PRÉSENCES ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendances (
    id          SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id)  ON DELETE CASCADE,
    student_id  INTEGER NOT NULL REFERENCES students(id)   ON DELETE CASCADE,
    status      VARCHAR(20) DEFAULT 'present',
    -- present | absent | retard | justifie
    recorded_at TIMESTAMP DEFAULT NOW(),
    recorded_by INTEGER REFERENCES users(id),
    note        TEXT,
    UNIQUE(schedule_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_attendance_schedule ON attendances(schedule_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student  ON attendances(student_id);

-- ─── 6. MESSAGES PROF → CLASSE ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS class_messages (
    id           SERIAL PRIMARY KEY,
    professor_id INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    class_id     INTEGER NOT NULL REFERENCES classes(id)    ON DELETE CASCADE,
    subject      VARCHAR(300) NOT NULL,
    body         TEXT         NOT NULL,
    is_urgent    BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_class ON class_messages(class_id);
CREATE INDEX IF NOT EXISTS idx_messages_prof  ON class_messages(professor_id);

-- ─── 7. RÉCLAMATIONS DE NOTES ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grade_claims (
    id          SERIAL PRIMARY KEY,
    grade_id    INTEGER NOT NULL REFERENCES grades(id)    ON DELETE CASCADE,
    student_id  INTEGER NOT NULL REFERENCES students(id)  ON DELETE CASCADE,
    reason      TEXT    NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
    -- pending | accepted | rejected
    response    TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    reviewed_by INTEGER REFERENCES professors(id)
);
CREATE INDEX IF NOT EXISTS idx_claims_student ON grade_claims(student_id);
CREATE INDEX IF NOT EXISTS idx_claims_status  ON grade_claims(status);
