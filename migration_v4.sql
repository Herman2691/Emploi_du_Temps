-- ============================================================
-- MIGRATION V4 — Noms séparés, username, import Excel
-- À exécuter dans Supabase SQL Editor (après migration_v3.sql)
-- ============================================================

-- 1. student_registry : séparer nom / postnom / prénom + promotion/option texte
ALTER TABLE student_registry
    ADD COLUMN IF NOT EXISTS nom           VARCHAR(100),
    ADD COLUMN IF NOT EXISTS postnom       VARCHAR(100),
    ADD COLUMN IF NOT EXISTS prenom        VARCHAR(100),
    ADD COLUMN IF NOT EXISTS promotion_txt VARCHAR(100),
    ADD COLUMN IF NOT EXISTS option_txt    VARCHAR(100);

-- Migrer les données existantes (full_name → nom)
UPDATE student_registry SET nom = full_name WHERE nom IS NULL AND full_name IS NOT NULL;

-- 2. students : séparer nom / postnom / prénom + username
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS nom     VARCHAR(100),
    ADD COLUMN IF NOT EXISTS postnom VARCHAR(100),
    ADD COLUMN IF NOT EXISTS prenom  VARCHAR(100),
    ADD COLUMN IF NOT EXISTS username VARCHAR(100);

-- Migrer les données existantes
UPDATE students SET nom = full_name WHERE nom IS NULL AND full_name IS NOT NULL;

-- Index unique sur username (nullable)
CREATE UNIQUE INDEX IF NOT EXISTS idx_students_username
    ON students(username) WHERE username IS NOT NULL;

-- Vérification
SELECT column_name FROM information_schema.columns
WHERE table_name IN ('student_registry','students')
  AND column_name IN ('nom','postnom','prenom','username','promotion_txt','option_txt')
ORDER BY table_name, column_name;
