-- migration_v26.sql
-- Cours liés à une promotion + professeur titulaire

ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS promotion_id INTEGER REFERENCES promotions(id),
    ADD COLUMN IF NOT EXISTS professor_id INTEGER REFERENCES professors(id);

CREATE INDEX IF NOT EXISTS idx_courses_promotion ON courses(promotion_id);
CREATE INDEX IF NOT EXISTS idx_courses_professor  ON courses(professor_id);

-- UE aussi promotion-spécifique
ALTER TABLE unites_enseignement
    ADD COLUMN IF NOT EXISTS promotion_id INTEGER REFERENCES promotions(id);

CREATE INDEX IF NOT EXISTS idx_ue_promotion ON unites_enseignement(promotion_id);
