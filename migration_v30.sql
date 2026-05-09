-- ============================================================
-- MIGRATION V30 — Refactorisation de la gestion des professeurs
-- Les professeurs appartiennent désormais à l'université (pool)
-- et sont affiliés aux facultés avec un statut permanent/visiteur
-- ============================================================

-- ── 1. Ajouter university_id aux professeurs ─────────────────────────────────
ALTER TABLE professors
    ADD COLUMN IF NOT EXISTS university_id INTEGER REFERENCES universities(id) ON DELETE CASCADE;

-- ── 2. Peupler university_id depuis les données existantes ───────────────────
--      professors → departments → faculties → universities
UPDATE professors p
SET university_id = u.id
FROM departments  d
JOIN faculties    f ON f.id = d.faculty_id
JOIN universities u ON u.id = f.university_id
WHERE d.id = p.department_id;

-- ── 3. Rendre university_id obligatoire ──────────────────────────────────────
ALTER TABLE professors
    ALTER COLUMN university_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_professors_university ON professors(university_id);

-- ── 4. Créer la table d'affiliation faculté ──────────────────────────────────
CREATE TABLE IF NOT EXISTS professor_faculty_affiliations (
    id           SERIAL PRIMARY KEY,
    professor_id INTEGER NOT NULL REFERENCES professors(id)  ON DELETE CASCADE,
    faculty_id   INTEGER NOT NULL REFERENCES faculties(id)   ON DELETE CASCADE,
    status       VARCHAR(20) NOT NULL DEFAULT 'permanent'
                 CHECK (status IN ('permanent', 'visiteur')),
    created_at   TIMESTAMP DEFAULT NOW(),
    UNIQUE(professor_id, faculty_id)
);

CREATE INDEX IF NOT EXISTS idx_pfa_professor ON professor_faculty_affiliations(professor_id);
CREATE INDEX IF NOT EXISTS idx_pfa_faculty   ON professor_faculty_affiliations(faculty_id);
CREATE INDEX IF NOT EXISTS idx_pfa_status    ON professor_faculty_affiliations(status);

-- ── 5. Migrer les affiliations existantes ────────────────────────────────────
--      Chaque prof existant reçoit une affiliation 'permanent'
--      à la faculté de son département actuel
INSERT INTO professor_faculty_affiliations (professor_id, faculty_id, status)
SELECT p.id, d.faculty_id, 'permanent'
FROM   professors  p
JOIN   departments d ON d.id = p.department_id
ON CONFLICT (professor_id, faculty_id) DO NOTHING;

-- ── 6. Mettre à jour le statut : 'Visiteur' → 'Contractuel' ─────────────────
--      Le concept 'Visiteur' est maintenant géré dans
--      professor_faculty_affiliations.status, pas sur le prof lui-même
UPDATE professors
SET statut = 'Contractuel'
WHERE statut = 'Visiteur';

-- ── 7. Mettre à jour la contrainte CHECK sur statut ──────────────────────────
--      Nouveaux types : Permanent (CDI), Contractuel (CDD), Vacataire
ALTER TABLE professors DROP CONSTRAINT IF EXISTS professors_statut_check;
UPDATE professors
SET statut = 'Contractuel'
WHERE statut NOT IN ('Permanent', 'Contractuel', 'Vacataire');
ALTER TABLE professors
    ADD CONSTRAINT professors_statut_check
    CHECK (statut IN ('Permanent', 'Contractuel', 'Vacataire'));

-- ── 8. Supprimer department_id de professors ─────────────────────────────────
DROP INDEX  IF EXISTS idx_professors_department;
ALTER TABLE professors DROP COLUMN IF EXISTS department_id;
