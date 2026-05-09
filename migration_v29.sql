-- migration_v29.sql
-- Consolidation : s'assure que toutes les colonnes requises existent sur students
-- Sûr à re-exécuter (IF NOT EXISTS)

-- Colonnes ajoutées par migration_v4 (nom, postnom, prenom, username)
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS nom      VARCHAR(100),
    ADD COLUMN IF NOT EXISTS postnom  VARCHAR(100),
    ADD COLUMN IF NOT EXISTS prenom   VARCHAR(100),
    ADD COLUMN IF NOT EXISTS username VARCHAR(100);

-- Index unique sur username (partiel : NULL autorisés, doublons interdits)
CREATE UNIQUE INDEX IF NOT EXISTS idx_students_username
    ON students(username) WHERE username IS NOT NULL;

-- Colonne registry_id (ajoutée par migration_v2)
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS registry_id INTEGER REFERENCES student_registry(id);

-- S'assure que student_registry a bien la colonne is_registered
ALTER TABLE student_registry
    ADD COLUMN IF NOT EXISTS is_registered BOOLEAN DEFAULT FALSE;

-- Synchroniser is_registered avec les comptes existants
UPDATE student_registry r
SET is_registered = TRUE
WHERE EXISTS (
    SELECT 1 FROM students s WHERE s.registry_id = r.id
)
AND is_registered = FALSE;
