-- ============================================================
-- SCRIPT D'INSERTION — UNIKIN
-- À exécuter dans Supabase SQL Editor
-- ============================================================

-- Extension pgcrypto pour le hashage du mot de passe
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- 1. UNIVERSITÉ
-- ============================================================
INSERT INTO universities (name, address, photo_url, website)
VALUES (
    'UNIKIN',
    'Kinshasa, République Démocratique du Congo',
    'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400',
    'https://unikin.ac.cd'
)
ON CONFLICT DO NOTHING
RETURNING id;


-- ============================================================
-- 2. FACULTÉ — Économie
-- ============================================================
INSERT INTO faculties (name, university_id, description)
SELECT
    'Économie',
    id,
    'Faculté des Sciences Économiques et de Gestion'
FROM universities
WHERE name = 'UNIKIN'
ON CONFLICT DO NOTHING;


-- ============================================================
-- 3. DÉPARTEMENT — IGAF
-- ============================================================
INSERT INTO departments (name, faculty_id, description)
SELECT
    'IGAF',
    f.id,
    'Informatique de Gestion et Anglais des Affaires'
FROM faculties f
JOIN universities u ON f.university_id = u.id
WHERE u.name = 'UNIKIN'
  AND f.name = 'Économie'
ON CONFLICT DO NOTHING;


-- ============================================================
-- 4. PROMOTION — L1
-- ============================================================
INSERT INTO promotions (name, academic_year, department_id)
SELECT
    'L1',
    '2024-2025',
    d.id
FROM departments d
JOIN faculties f    ON d.faculty_id    = f.id
JOIN universities u ON f.university_id = u.id
WHERE u.name = 'UNIKIN'
  AND f.name = 'Économie'
  AND d.name = 'IGAF'
ON CONFLICT DO NOTHING;


-- ============================================================
-- 5. ADMIN DÉPARTEMENT — Herman
--    Mot de passe : incorrecte  (hashé avec bcrypt via pgcrypto)
-- ============================================================
INSERT INTO users (name, email, password_hash, role, university_id, faculty_id, department_id)
SELECT
    'Herman',
    'planetherman2022@gmail.com',
    crypt('incorrecte', gen_salt('bf', 12)),   -- bcrypt rounds=12
    'admin_departement',
    u.id,
    f.id,
    d.id
FROM departments d
JOIN faculties f    ON d.faculty_id    = f.id
JOIN universities u ON f.university_id = u.id
WHERE u.name = 'UNIKIN'
  AND f.name = 'Économie'
  AND d.name = 'IGAF'
ON CONFLICT (email) DO NOTHING;


-- ============================================================
-- VÉRIFICATION — Affiche ce qui a été inséré
-- ============================================================
SELECT
    u.name  AS université,
    f.name  AS faculté,
    d.name  AS département,
    p.name  AS promotion,
    p.academic_year
FROM promotions p
JOIN departments d  ON p.department_id = d.id
JOIN faculties f    ON d.faculty_id    = f.id
JOIN universities u ON f.university_id = u.id
WHERE u.name = 'UNIKIN';

SELECT id, name, email, role FROM users WHERE email = 'planetherman2022@gmail.com';
