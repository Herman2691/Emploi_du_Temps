-- migration_v6.sql
-- Lie les documents de cours aux promotions (pas aux classes/salles)

ALTER TABLE course_documents
    DROP COLUMN IF EXISTS class_id,
    ADD COLUMN IF NOT EXISTS promotion_id INTEGER REFERENCES promotions(id) ON DELETE SET NULL;
