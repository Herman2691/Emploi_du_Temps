-- migration_v34.sql
-- Messagerie étudiant → admin + tokens QR pour présences

CREATE TABLE IF NOT EXISTS student_messages (
    id            SERIAL PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students(id)    ON DELETE CASCADE,
    department_id INTEGER          REFERENCES departments(id) ON DELETE SET NULL,
    subject       VARCHAR(200)     NOT NULL,
    body          TEXT             NOT NULL,
    is_read       BOOLEAN          NOT NULL DEFAULT FALSE,
    reply         TEXT             DEFAULT NULL,
    replied_at    TIMESTAMP        DEFAULT NULL,
    created_at    TIMESTAMP        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_msgs_student ON student_messages(student_id);
CREATE INDEX IF NOT EXISTS idx_student_msgs_dept    ON student_messages(department_id);
CREATE INDEX IF NOT EXISTS idx_student_msgs_read    ON student_messages(is_read);

CREATE TABLE IF NOT EXISTS attendance_tokens (
    id            SERIAL PRIMARY KEY,
    schedule_id   INTEGER NOT NULL REFERENCES schedules(id)  ON DELETE CASCADE,
    token         VARCHAR(10) NOT NULL UNIQUE,
    session_date  DATE        NOT NULL,
    created_by    INTEGER     REFERENCES users(id)           ON DELETE SET NULL,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    expires_at    TIMESTAMP   NOT NULL,
    created_at    TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_att_tokens_token  ON attendance_tokens(token);
CREATE INDEX IF NOT EXISTS idx_att_tokens_active ON attendance_tokens(is_active);
