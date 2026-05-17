-- migration_v33.sql
-- Frais académiques : types de frais + frais par étudiant

CREATE TABLE IF NOT EXISTS fee_types (
    id            SERIAL PRIMARY KEY,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name          VARCHAR(150) NOT NULL,
    amount        NUMERIC(10,2) NOT NULL DEFAULT 0,
    currency      VARCHAR(10)  NOT NULL DEFAULT '$',
    is_mandatory  BOOLEAN      NOT NULL DEFAULT FALSE,
    academic_year VARCHAR(20)  DEFAULT NULL,
    description   TEXT         DEFAULT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fee_types_university ON fee_types(university_id);
CREATE INDEX IF NOT EXISTS idx_fee_types_year       ON fee_types(academic_year);

CREATE TABLE IF NOT EXISTS student_fees (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER      NOT NULL REFERENCES students(id)  ON DELETE CASCADE,
    fee_type_id INTEGER      NOT NULL REFERENCES fee_types(id) ON DELETE CASCADE,
    amount      NUMERIC(10,2) DEFAULT NULL,
    is_paid     BOOLEAN      NOT NULL DEFAULT FALSE,
    paid_at     TIMESTAMP    DEFAULT NULL,
    paid_by     INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    notes       VARCHAR(255) DEFAULT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, fee_type_id)
);

CREATE INDEX IF NOT EXISTS idx_student_fees_student  ON student_fees(student_id);
CREATE INDEX IF NOT EXISTS idx_student_fees_fee_type ON student_fees(fee_type_id);
CREATE INDEX IF NOT EXISTS idx_student_fees_paid     ON student_fees(is_paid);
