-- migration_v22.sql
-- Statut académique directement sur student_registry

ALTER TABLE student_registry
    ADD COLUMN IF NOT EXISTS statut VARCHAR(20) DEFAULT 'inscrit';
-- Valeurs : inscrit | admis | redoublant | transfere | abandonne

-- Mettre à jour les existants
UPDATE student_registry SET statut = 'inscrit' WHERE statut IS NULL;

CREATE INDEX IF NOT EXISTS idx_registry_statut ON student_registry(statut);
