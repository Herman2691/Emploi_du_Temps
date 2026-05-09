-- migration_v12.sql : Types de créneaux (cours / examen / ferie)

ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS slot_type  VARCHAR(20) NOT NULL DEFAULT 'cours',
    ADD COLUMN IF NOT EXISTS slot_label VARCHAR(200) DEFAULT NULL;

-- Les jours fériés n'ont pas de cours ni de professeur
ALTER TABLE schedules ALTER COLUMN course_id    DROP NOT NULL;
ALTER TABLE schedules ALTER COLUMN professor_id DROP NOT NULL;

-- Index pour filtrage par type
CREATE INDEX IF NOT EXISTS idx_schedules_slot_type ON schedules(slot_type);
