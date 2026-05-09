-- migration_v13.sql
-- Status annulation/remplacement sur les créneaux
ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS slot_status VARCHAR(20) NOT NULL DEFAULT 'actif',
    ADD COLUMN IF NOT EXISTS cancel_note TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS substitute_professor_id INTEGER REFERENCES professors(id) DEFAULT NULL;

-- Historique des modifications
CREATE TABLE IF NOT EXISTS schedule_audit (
    id          SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL,
    action      VARCHAR(20) NOT NULL,  -- 'create','update','cancel','substitute','delete'
    changed_by  VARCHAR(100),
    changed_at  TIMESTAMP DEFAULT NOW(),
    old_values  JSONB,
    new_values  JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_schedule ON schedule_audit(schedule_id);
CREATE INDEX IF NOT EXISTS idx_audit_date ON schedule_audit(changed_at);
