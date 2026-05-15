-- migration_v31.sql
-- Point 9 : colonne pdf_url sur la table bulletins
--           pour l'import de bulletins PDF par le département

ALTER TABLE bulletins
    ADD COLUMN IF NOT EXISTS pdf_url TEXT DEFAULT NULL;
