-- ============================================================
-- MIGRATION V11 — Période de validité des créneaux horaires
-- ============================================================

-- Ajouter valid_from et valid_until aux schedules
-- NULL = cours récurrent sans limite (comportement actuel conservé)
ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS valid_from  DATE DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS valid_until DATE DEFAULT NULL;

-- Index pour filtrage rapide par date
CREATE INDEX IF NOT EXISTS idx_schedules_valid_from  ON schedules(valid_from);
CREATE INDEX IF NOT EXISTS idx_schedules_valid_until ON schedules(valid_until);
