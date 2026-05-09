-- ============================================================
-- MIGRATION V3 — Couleur personnalisée par université
-- À exécuter dans Supabase SQL Editor (après migration_v2.sql)
-- ============================================================

ALTER TABLE universities
    ADD COLUMN IF NOT EXISTS primary_color VARCHAR(7) DEFAULT '#2563EB';
