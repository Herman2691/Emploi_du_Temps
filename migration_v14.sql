-- migration_v14.sql : Audit trail des notes

CREATE TABLE IF NOT EXISTS grade_audit (
    id                      SERIAL PRIMARY KEY,
    student_id              INTEGER NOT NULL,
    course_id               INTEGER NOT NULL,
    exam_type               VARCHAR(50),
    session_name            VARCHAR(100),
    old_grade               NUMERIC(5,2),
    new_grade               NUMERIC(5,2) NOT NULL,
    max_grade               NUMERIC(5,2),
    changed_by_professor_id INTEGER REFERENCES professors(id),
    changed_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grade_audit_student  ON grade_audit(student_id);
CREATE INDEX IF NOT EXISTS idx_grade_audit_course   ON grade_audit(course_id);
CREATE INDEX IF NOT EXISTS idx_grade_audit_changed  ON grade_audit(changed_at);
