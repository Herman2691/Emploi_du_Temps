-- migration_v7.sql
-- Ajout du statut professeur : Visiteur ou Contractuel

ALTER TABLE professors
ADD COLUMN IF NOT EXISTS statut VARCHAR(20) DEFAULT 'Contractuel'
CHECK (statut IN ('Visiteur', 'Contractuel'));
