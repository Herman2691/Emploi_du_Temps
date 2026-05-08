-- migration_v20.sql
-- Table de référence des années académiques par université

CREATE TABLE IF NOT EXISTS academic_years (
    id            SERIAL PRIMARY KEY,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    label         VARCHAR(9) NOT NULL,          -- ex: "2024-2025"
    start_date    DATE,
    end_date      DATE,
    is_current    BOOLEAN NOT NULL DEFAULT FALSE,
    status        VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | archived | planned
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(university_id, label)
);

CREATE INDEX IF NOT EXISTS idx_ay_university ON academic_years(university_id);
-- Garantit qu'une seule année est courante par université
CREATE UNIQUE INDEX IF NOT EXISTS idx_ay_current_unique
    ON academic_years(university_id)
    WHERE is_current = TRUE;
