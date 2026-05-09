-- migration_v24.sql
-- Renommer ecole_provenance → provenance
-- (sert à la fois pour les recrus: nom de l'école, et les montantes: nom de la promotion source)

ALTER TABLE student_registry
    RENAME COLUMN ecole_provenance TO provenance;

COMMENT ON COLUMN student_registry.provenance IS
    'Recrutement: école/lycée d''origine. Montante: promotion source (ex: L1 Informatique).';
