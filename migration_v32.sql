-- migration_v32.sql
-- Profil étudiant enrichi : informations personnelles, adresse, contact urgence, diplôme, photo

ALTER TABLE student_registry
    ADD COLUMN IF NOT EXISTS telephone              VARCHAR(30)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS lieu_naissance         VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS nationalite            VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS etat_civil             VARCHAR(30)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS province               VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS district               VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS territoire             VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS secteur                VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS commune                VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS adresse_domicile       VARCHAR(150) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS contact_urgence_nom    VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS contact_urgence_tel    VARCHAR(30)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS contact_urgence_adresse VARCHAR(150) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS diplome_type           VARCHAR(50)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS diplome_numero         VARCHAR(80)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS diplome_section        VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS diplome_etablissement  VARCHAR(150) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS diplome_annee          VARCHAR(20)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS photo_passeport_url    TEXT         DEFAULT NULL;

ALTER TABLE students
    ADD COLUMN IF NOT EXISTS telephone VARCHAR(30) DEFAULT NULL;
