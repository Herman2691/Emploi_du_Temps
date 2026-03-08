-- ============================================================
-- PLATEFORME MULTI-UNIVERSITÉS - SCHÉMA COMPLET
-- Version: 1.0.0
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLES PRINCIPALES
-- ============================================================

CREATE TABLE IF NOT EXISTS universities (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    address     TEXT,
    photo_url   TEXT,
    website     VARCHAR(255),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS faculties (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    university_id   INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    description     TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    faculty_id  INTEGER NOT NULL REFERENCES faculties(id) ON DELETE CASCADE,
    description TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS promotions (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    academic_year   VARCHAR(20) NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS classes (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    promotion_id    INTEGER NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    capacity        INTEGER DEFAULT 30,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS professors (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(50),
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS courses (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    code            VARCHAR(50),
    hours           INTEGER DEFAULT 0,
    weight          FLOAT DEFAULT 1.0,
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedules (
    id              SERIAL PRIMARY KEY,
    day             VARCHAR(20) NOT NULL CHECK (day IN ('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')),
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    room            VARCHAR(100),
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    professor_id    INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    class_id        INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    week_type       VARCHAR(20) DEFAULT 'Toutes',  -- Toutes, Paire, Impaire
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    CONSTRAINT no_overlap CHECK (start_time < end_time)
);

CREATE TABLE IF NOT EXISTS announcements (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    content         TEXT NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    is_pinned       BOOLEAN DEFAULT FALSE,
    expires_at      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE UTILISATEURS (ADMINS)
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(50) NOT NULL CHECK (role IN ('super_admin','admin_universite','admin_faculte','admin_departement')),
    university_id   INTEGER REFERENCES universities(id) ON DELETE SET NULL,
    faculty_id      INTEGER REFERENCES faculties(id) ON DELETE SET NULL,
    department_id   INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEX POUR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_faculties_university ON faculties(university_id);
CREATE INDEX IF NOT EXISTS idx_departments_faculty ON departments(faculty_id);
CREATE INDEX IF NOT EXISTS idx_promotions_department ON promotions(department_id);
CREATE INDEX IF NOT EXISTS idx_classes_promotion ON classes(promotion_id);
CREATE INDEX IF NOT EXISTS idx_schedules_class ON schedules(class_id);
CREATE INDEX IF NOT EXISTS idx_schedules_day ON schedules(day);
CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department_id);
CREATE INDEX IF NOT EXISTS idx_professors_department ON professors(department_id);
CREATE INDEX IF NOT EXISTS idx_announcements_department ON announcements(department_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================
-- TRIGGERS - updated_at automatique
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['universities','faculties','departments','promotions',
                              'classes','professors','courses','schedules',
                              'announcements','users']
    LOOP
        -- Crée le trigger seulement s'il n'existe pas déjà (évite les NOTICE)
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            JOIN pg_class ON pg_class.oid = pg_trigger.tgrelid
            WHERE pg_trigger.tgname = 'trg_' || t || '_updated'
              AND pg_class.relname  = t
        ) THEN
            EXECUTE format('
                CREATE TRIGGER trg_%s_updated
                BEFORE UPDATE ON %s
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            ', t, t);
        END IF;
    END LOOP;
END;
$$;

-- ============================================================
-- DONNÉES DE DÉMO
-- ============================================================

-- Super Admin (password: Admin@1234)
INSERT INTO users (name, email, password_hash, role) VALUES
('Super Administrateur', 'superadmin@platform.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlEd3kMQvnMLbD5RJvGMKO.Dm', 'super_admin')
ON CONFLICT (email) DO NOTHING;

-- Université de démo
INSERT INTO universities (name, address, photo_url, website) VALUES
('Université des Sciences et Technologies', 'Avenue de l''Université, Alger', 
 'https://images.unsplash.com/photo-1562774053-701939374585?w=400', 'https://ust.dz'),
('Université Centrale', '10 Rue de la République, Oran',
 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400', 'https://uc.dz')
ON CONFLICT DO NOTHING;
