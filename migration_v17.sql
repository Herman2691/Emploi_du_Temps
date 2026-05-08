-- migration_v17.sql
-- Workflow statut des notes : brouillon → soumis → valide → publie
-- + table bulletins (publication officielle par session)

-- ─── 1. COLONNE STATUS SUR LES NOTES ─────────────────────────────────────────
ALTER TABLE grades ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'brouillon';
-- Valeurs : brouillon | soumis | valide | publie

-- Synchroniser avec les données existantes
UPDATE grades SET status = 'publie'    WHERE is_published = TRUE  AND status = 'brouillon';
-- Les notes non publiées restent 'brouillon'

CREATE INDEX IF NOT EXISTS idx_grades_status ON grades(status);

-- ─── 2. TABLE BULLETINS ───────────────────────────────────────────────────────
-- Un bulletin = publication officielle d'une session pour une classe
CREATE TABLE IF NOT EXISTS bulletins (
    id              SERIAL PRIMARY KEY,
    class_id        INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_name    VARCHAR(100) NOT NULL,
    academic_year   VARCHAR(9)   NOT NULL,  -- ex : "2024-2025"
    status          VARCHAR(20)  DEFAULT 'brouillon',
    -- brouillon | valide | publie
    notes           TEXT,                   -- remarques libres du département
    created_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    validated_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    validated_at    TIMESTAMP,
    published_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    published_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(class_id, session_name, academic_year)
);
CREATE INDEX IF NOT EXISTS idx_bulletins_class  ON bulletins(class_id);
CREATE INDEX IF NOT EXISTS idx_bulletins_status ON bulletins(status);
