-- migration_v27.sql
-- Contrainte UNIQUE sur courses.code (NULL autorisé, doublons non)

-- Supprimer les doublons éventuels en gardant le plus récent
DELETE FROM courses
WHERE id NOT IN (
    SELECT MAX(id)
    FROM courses
    WHERE code IS NOT NULL
    GROUP BY code
)
AND code IS NOT NULL;

-- Ajouter la contrainte UNIQUE (les NULL ne comptent pas comme doublons en PG)
ALTER TABLE courses
    ADD CONSTRAINT courses_code_unique UNIQUE (code);
