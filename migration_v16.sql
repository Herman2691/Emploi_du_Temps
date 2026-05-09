-- migration_v16.sql
-- Gestion de la modification des cotes avec règle des 48h,
-- historique complet et demandes de validation admin

-- ─── 1. HORODATAGE DES NOTES ──────────────────────────────────────────────────
-- created_at = moment où la note a été saisie pour la première fois
-- updated_at = moment de la dernière modification directe
ALTER TABLE grades ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE grades ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Rétrocompatibilité : renseigner created_at pour les lignes existantes
UPDATE grades SET created_at = NOW() WHERE created_at IS NULL;

-- ─── 2. AMÉLIORATION DE grade_audit ──────────────────────────────────────────
-- Ajouter les champs manquants pour un historique complet
ALTER TABLE grade_audit ADD COLUMN IF NOT EXISTS motif        TEXT;
ALTER TABLE grade_audit ADD COLUMN IF NOT EXISTS action       VARCHAR(20) DEFAULT 'update';
-- action: create | update | delete | request_approved | request_rejected
ALTER TABLE grade_audit ADD COLUMN IF NOT EXISTS old_max_grade   NUMERIC(5,2);
ALTER TABLE grade_audit ADD COLUMN IF NOT EXISTS old_comment      TEXT;
ALTER TABLE grade_audit ADD COLUMN IF NOT EXISTS new_comment      TEXT;
ALTER TABLE grade_audit ADD COLUMN IF NOT EXISTS reviewed_by_id   INTEGER REFERENCES users(id);

-- ─── 3. DEMANDES DE MODIFICATION (après 48h) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS grade_modification_requests (
    id               SERIAL PRIMARY KEY,
    grade_id         INTEGER NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    professor_id     INTEGER NOT NULL REFERENCES professors(id),
    -- valeurs actuelles (snapshot)
    current_grade    NUMERIC(5,2),
    current_max      NUMERIC(5,2),
    current_comment  TEXT,
    -- valeurs demandées
    requested_grade   NUMERIC(5,2) NOT NULL,
    requested_max     NUMERIC(5,2),
    requested_comment TEXT,
    motif            TEXT NOT NULL,
    -- traitement admin
    status           VARCHAR(20) DEFAULT 'pending',
    -- pending | approved | rejected
    admin_response   TEXT,
    reviewed_by      INTEGER REFERENCES users(id),
    reviewed_at      TIMESTAMP,
    requested_at     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grade_mod_grade   ON grade_modification_requests(grade_id);
CREATE INDEX IF NOT EXISTS idx_grade_mod_prof    ON grade_modification_requests(professor_id);
CREATE INDEX IF NOT EXISTS idx_grade_mod_status  ON grade_modification_requests(status);
