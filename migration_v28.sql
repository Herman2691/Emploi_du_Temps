-- migration_v28.sql
-- Gestion des salles physiques

CREATE TABLE IF NOT EXISTS rooms (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    code          VARCHAR(20),
    capacity      INTEGER DEFAULT 0,
    room_type     VARCHAR(30) DEFAULT 'salle',
    building      VARCHAR(50),
    floor         VARCHAR(20),
    university_id INTEGER REFERENCES universities(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rooms_code_uni
    ON rooms(code, university_id) WHERE code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rooms_university ON rooms(university_id);
CREATE INDEX IF NOT EXISTS idx_rooms_department ON rooms(department_id);

-- Ajouter room_id sur schedules (garde l'ancien champ texte pour compatibilité)
ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS room_id INTEGER REFERENCES rooms(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_schedules_room ON schedules(room_id);

-- Trigger updated_at
CREATE OR REPLACE TRIGGER trg_rooms_updated
    BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
