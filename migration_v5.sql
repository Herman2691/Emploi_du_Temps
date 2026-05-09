-- ============================================================
-- MIGRATION V5 — PDF pour les communiqués
-- À exécuter dans Supabase SQL Editor (après migration_v4.sql)
-- ============================================================

ALTER TABLE announcements
    ADD COLUMN IF NOT EXISTS file_url  TEXT,
    ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
