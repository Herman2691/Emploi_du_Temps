-- migration_v18.sql
-- Liste d'inscription enrichie : département, filière, option, promotion,
-- année académique, école de provenance, date de naissance, sexe

ALTER TABLE student_registry
    ADD COLUMN IF NOT EXISTS department_id    INTEGER REFERENCES departments(id)   ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS filiere_id       INTEGER REFERENCES filieres(id)       ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS option_id        INTEGER REFERENCES options_etude(id)  ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS promotion_id     INTEGER REFERENCES promotions(id)     ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS annee_academique VARCHAR(9),      -- ex : "2024-2025"
    ADD COLUMN IF NOT EXISTS ecole_provenance VARCHAR(200),    -- école/lycée d'origine
    ADD COLUMN IF NOT EXISTS date_naissance   DATE,
    ADD COLUMN IF NOT EXISTS sexe             VARCHAR(10);     -- M | F | Autre

-- Index pour les filtres fréquents
CREATE INDEX IF NOT EXISTS idx_registry_dept     ON student_registry(department_id);
CREATE INDEX IF NOT EXISTS idx_registry_filiere  ON student_registry(filiere_id);
CREATE INDEX IF NOT EXISTS idx_registry_option   ON student_registry(option_id);
CREATE INDEX IF NOT EXISTS idx_registry_promo    ON student_registry(promotion_id);
CREATE INDEX IF NOT EXISTS idx_registry_annee    ON student_registry(annee_academique);
