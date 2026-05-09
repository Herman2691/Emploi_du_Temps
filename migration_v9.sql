-- ============================================================
-- MIGRATION V9 — Communiqués université + auteur
-- ============================================================

-- Rendre department_id optionnel (annonces niveau université n'ont pas de département)
ALTER TABLE announcements
    ALTER COLUMN department_id DROP NOT NULL;

-- Ajouter université et auteur
ALTER TABLE announcements
    ADD COLUMN IF NOT EXISTS university_id INTEGER REFERENCES universities(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS created_by    INTEGER REFERENCES users(id)        ON DELETE SET NULL;

-- Index pour les requêtes par université
CREATE INDEX IF NOT EXISTS idx_announcements_university ON announcements(university_id);
