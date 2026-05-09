# db/queries.py
from db.connection import execute_query

# Noms de session standardisés LMD
SESSION_NAMES = [
    "S1 - Session Normale",
    "S1 - Session de Rattrapage",
    "S2 - Session Normale",
    "S2 - Session de Rattrapage",
]
# Rattrapage → Session normale correspondante
RATTRAPAGE_MAP = {
    "S1 - Session de Rattrapage": "S1 - Session Normale",
    "S2 - Session de Rattrapage": "S2 - Session Normale",
}


# ============================================================
# UNIVERSITÉS
# ============================================================
class UniversityQueries:

    @staticmethod
    def get_all(active_only=True):
        sql = "SELECT * FROM universities"
        if active_only:
            sql += " WHERE is_active = TRUE"
        sql += " ORDER BY name"
        return execute_query(sql)

    @staticmethod
    def get_by_id(university_id: int):
        return execute_query(
            "SELECT * FROM universities WHERE id = %s",
            (university_id,), fetch="one"
        )

    @staticmethod
    def create(name, address, photo_url, website, primary_color="#2563EB"):
        return execute_query(
            "INSERT INTO universities (name,address,photo_url,website,primary_color) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (name, address or None, photo_url or None,
             website or None, primary_color or "#2563EB"), fetch="one"
        )

    @staticmethod
    def update(university_id, name, address, photo_url, website, primary_color="#2563EB"):
        execute_query(
            "UPDATE universities SET name=%s,address=%s,photo_url=%s,website=%s,"
            "primary_color=%s WHERE id=%s",
            (name, address or None, photo_url or None,
             website or None, primary_color or "#2563EB", university_id), fetch="none"
        )

    @staticmethod
    def get_platform_stats():
        return execute_query("""
            SELECT
                (SELECT COUNT(*) FROM universities  WHERE is_active=TRUE) AS uni_count,
                (SELECT COUNT(*) FROM professors    WHERE is_active=TRUE) AS prof_count,
                (SELECT COUNT(*) FROM schedules     WHERE is_active=TRUE) AS schedule_count,
                (SELECT COUNT(*) FROM students      WHERE is_active=TRUE) AS student_count
        """, fetch="one")

    @staticmethod
    def delete(university_id):
        execute_query("UPDATE universities SET is_active=FALSE WHERE id=%s",
                      (university_id,), fetch="none")

    @staticmethod
    def get_stats(university_id):
        return execute_query("""
            SELECT
                (SELECT COUNT(*) FROM faculties     WHERE university_id=%s AND is_active=TRUE) AS faculties_count,
                (SELECT COUNT(*) FROM departments d
                 JOIN faculties f ON d.faculty_id=f.id
                 WHERE f.university_id=%s AND d.is_active=TRUE)  AS departments_count,
                (SELECT COUNT(*) FROM promotions pr
                 JOIN departments d  ON pr.department_id=d.id
                 JOIN faculties f    ON d.faculty_id=f.id
                 WHERE f.university_id=%s AND pr.is_active=TRUE) AS promotions_count
        """, (university_id, university_id, university_id), fetch="one")


# ============================================================
# FACULTÉS
# ============================================================
class FacultyQueries:

    @staticmethod
    def get_by_university(university_id):
        return execute_query(
            "SELECT * FROM faculties WHERE university_id=%s AND is_active=TRUE ORDER BY name",
            (university_id,)
        )

    @staticmethod
    def get_by_id(faculty_id):
        return execute_query(
            "SELECT f.*, u.name AS university_name FROM faculties f "
            "JOIN universities u ON f.university_id=u.id WHERE f.id=%s",
            (faculty_id,), fetch="one"
        )

    @staticmethod
    def create(name, university_id, description=""):
        return execute_query(
            "INSERT INTO faculties (name,university_id,description) VALUES (%s,%s,%s) RETURNING id",
            (name, university_id, description or ""), fetch="one"
        )

    @staticmethod
    def update(faculty_id, name, description=""):
        execute_query(
            "UPDATE faculties SET name=%s,description=%s WHERE id=%s",
            (name, description or "", faculty_id), fetch="none"
        )

    @staticmethod
    def delete(faculty_id):
        execute_query("UPDATE faculties SET is_active=FALSE WHERE id=%s",
                      (faculty_id,), fetch="none")


# ============================================================
# DÉPARTEMENTS
# ============================================================
class DepartmentQueries:

    @staticmethod
    def get_by_university(university_id):
        return execute_query(
            "SELECT d.*, f.name AS faculty_name FROM departments d "
            "JOIN faculties f ON d.faculty_id=f.id "
            "WHERE f.university_id=%s AND d.is_active=TRUE ORDER BY f.name, d.name",
            (university_id,)
        )

    @staticmethod
    def get_by_faculty(faculty_id):
        return execute_query(
            "SELECT * FROM departments WHERE faculty_id=%s AND is_active=TRUE ORDER BY name",
            (faculty_id,)
        )

    @staticmethod
    def get_by_id(department_id):
        return execute_query(
            "SELECT d.*, f.id AS faculty_id_fk, f.name AS faculty_name, "
            "u.id AS university_id, u.name AS university_name "
            "FROM departments d "
            "JOIN faculties f ON d.faculty_id=f.id "
            "JOIN universities u ON f.university_id=u.id "
            "WHERE d.id=%s",
            (department_id,), fetch="one"
        )

    @staticmethod
    def create(name, faculty_id, description=""):
        return execute_query(
            "INSERT INTO departments (name,faculty_id,description) VALUES (%s,%s,%s) RETURNING id",
            (name, faculty_id, description or ""), fetch="one"
        )

    @staticmethod
    def update(department_id, name, description=""):
        execute_query(
            "UPDATE departments SET name=%s,description=%s WHERE id=%s",
            (name, description or "", department_id), fetch="none"
        )

    @staticmethod
    def delete(department_id):
        execute_query("UPDATE departments SET is_active=FALSE WHERE id=%s",
                      (department_id,), fetch="none")


# ============================================================
# PROMOTIONS
# ============================================================
class PromotionQueries:

    @staticmethod
    def get_by_department(department_id):
        return execute_query(
            "SELECT * FROM promotions WHERE department_id=%s AND is_active=TRUE ORDER BY name",
            (department_id,)
        )

    @staticmethod
    def get_by_id(promotion_id):
        return execute_query(
            "SELECT * FROM promotions WHERE id=%s",
            (promotion_id,), fetch="one"
        )

    @staticmethod
    def create(name, academic_year, department_id, is_recrutement=False):
        return execute_query(
            "INSERT INTO promotions (name,academic_year,department_id,is_recrutement) "
            "VALUES (%s,%s,%s,%s) RETURNING id",
            (name, academic_year, department_id, is_recrutement), fetch="one"
        )

    @staticmethod
    def update(promotion_id, name, academic_year, is_recrutement=False):
        execute_query(
            "UPDATE promotions SET name=%s,academic_year=%s,is_recrutement=%s WHERE id=%s",
            (name, academic_year, is_recrutement, promotion_id), fetch="none"
        )

    @staticmethod
    def delete(promotion_id):
        execute_query("UPDATE promotions SET is_active=FALSE WHERE id=%s",
                      (promotion_id,), fetch="none")


# ============================================================
# CLASSES
# ============================================================
class ClassQueries:

    @staticmethod
    def get_by_promotion(promotion_id):
        return execute_query(
            "SELECT * FROM classes WHERE promotion_id=%s AND is_active=TRUE ORDER BY name",
            (promotion_id,)
        )

    @staticmethod
    def get_by_id(class_id):
        return execute_query(
            "SELECT c.*, pr.name AS promotion_name, pr.academic_year, "
            "d.name AS department_name, f.name AS faculty_name, u.name AS university_name "
            "FROM classes c "
            "JOIN promotions pr ON c.promotion_id=pr.id "
            "JOIN departments d ON pr.department_id=d.id "
            "JOIN faculties f   ON d.faculty_id=f.id "
            "JOIN universities u ON f.university_id=u.id "
            "WHERE c.id=%s",
            (class_id,), fetch="one"
        )

    @staticmethod
    def get_by_id_full(class_id):
        """Retourne la classe avec tous les IDs et noms des entités parentes."""
        return execute_query("""
            SELECT c.id, c.name, c.capacity,
                   pr.id  AS promotion_id,  pr.name AS promotion_name,
                   pr.academic_year,
                   d.id   AS department_id, d.name  AS department_name,
                   f.id   AS faculty_id,    f.name  AS faculty_name,
                   u.id   AS university_id, u.name  AS university_name
            FROM classes c
            JOIN promotions  pr ON c.promotion_id   = pr.id
            JOIN departments d  ON pr.department_id = d.id
            JOIN faculties   f  ON d.faculty_id     = f.id
            JOIN universities u ON f.university_id  = u.id
            WHERE c.id = %s
        """, (class_id,), fetch="one")

    @staticmethod
    def create(name, promotion_id, capacity=30):
        return execute_query(
            "INSERT INTO classes (name,promotion_id,capacity) VALUES (%s,%s,%s) RETURNING id",
            (name, promotion_id, capacity), fetch="one"
        )

    @staticmethod
    def update(class_id, name, capacity):
        execute_query(
            "UPDATE classes SET name=%s,capacity=%s WHERE id=%s",
            (name, capacity, class_id), fetch="none"
        )

    @staticmethod
    def delete(class_id):
        execute_query("UPDATE classes SET is_active=FALSE WHERE id=%s",
                      (class_id,), fetch="none")


# ============================================================
# PROFESSEURS
# ============================================================
class ProfessorQueries:

    @staticmethod
    def get_by_university(university_id):
        """Tous les profs du pool universitaire avec affiliations faculté + info compte."""
        return execute_query("""
            SELECT p.*,
                   STRING_AGG(f.name || ' (' || pfa.status || ')', ', '
                              ORDER BY pfa.status, f.name) AS affiliations,
                   u.id        AS user_id,
                   u.email     AS account_email,
                   u.is_active AS account_active
            FROM professors p
            LEFT JOIN professor_faculty_affiliations pfa ON pfa.professor_id = p.id
            LEFT JOIN faculties f ON f.id = pfa.faculty_id
            LEFT JOIN users u ON u.professor_id = p.id AND u.role = 'professeur'
            WHERE p.university_id = %s
            GROUP BY p.id, u.id, u.email, u.is_active
            ORDER BY p.name
        """, (university_id,))

    @staticmethod
    def get_unaffiliated(university_id, faculty_id):
        """Profs de l'université pas encore affiliés à cette faculté (pool disponible)."""
        return execute_query("""
            SELECT p.*
            FROM professors p
            WHERE p.university_id = %s AND p.is_active = TRUE
              AND NOT EXISTS (
                SELECT 1 FROM professor_faculty_affiliations pfa
                WHERE pfa.professor_id = p.id AND pfa.faculty_id = %s
              )
            ORDER BY p.name
        """, (university_id, faculty_id))

    @staticmethod
    def get_by_faculty(faculty_id):
        """Profs affiliés à une faculté (permanent + visiteur) avec info compte."""
        return execute_query("""
            SELECT p.*,
                   pfa.status    AS affiliation_status,
                   u.id          AS user_id,
                   u.email       AS account_email,
                   u.is_active   AS account_active
            FROM professors p
            JOIN professor_faculty_affiliations pfa ON pfa.professor_id = p.id
            LEFT JOIN users u ON u.professor_id = p.id AND u.role = 'professeur'
            WHERE pfa.faculty_id = %s AND p.is_active = TRUE
            ORDER BY pfa.status, p.name
        """, (faculty_id,))

    @staticmethod
    def get_by_department(department_id):
        """Profs affiliés à la faculté de ce département (pour l'admin département)."""
        return execute_query("""
            SELECT DISTINCT p.*,
                   pfa.status AS affiliation_status,
                   u.id       AS user_id,
                   u.email    AS account_email,
                   u.is_active AS account_active
            FROM professors p
            JOIN professor_faculty_affiliations pfa ON pfa.professor_id = p.id
            JOIN departments d ON d.faculty_id = pfa.faculty_id
            LEFT JOIN users u ON u.professor_id = p.id AND u.role = 'professeur'
            WHERE d.id = %s AND p.is_active = TRUE
            ORDER BY p.name
        """, (department_id,))

    @staticmethod
    def get_by_id(professor_id):
        return execute_query(
            "SELECT * FROM professors WHERE id=%s",
            (professor_id,), fetch="one"
        )

    @staticmethod
    def create(name, email, phone, university_id, statut="Contractuel"):
        return execute_query(
            "INSERT INTO professors (name, email, phone, university_id, statut) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, email or None, phone or None, university_id, statut), fetch="one"
        )

    @staticmethod
    def update(professor_id, name, email, phone, statut="Contractuel"):
        execute_query(
            "UPDATE professors SET name=%s, email=%s, phone=%s, statut=%s WHERE id=%s",
            (name, email or None, phone or None, statut, professor_id), fetch="none"
        )

    @staticmethod
    def set_active(professor_id, is_active: bool):
        execute_query("UPDATE professors SET is_active=%s WHERE id=%s",
                      (is_active, professor_id), fetch="none")

    @staticmethod
    def delete(professor_id):
        execute_query("UPDATE professors SET is_active=FALSE WHERE id=%s",
                      (professor_id,), fetch="none")


# ============================================================
# AFFILIATIONS PROFESSEUR ↔ FACULTÉ
# ============================================================
class ProfessorFacultyAffiliationQueries:

    @staticmethod
    def create(professor_id, faculty_id, status="permanent"):
        return execute_query("""
            INSERT INTO professor_faculty_affiliations (professor_id, faculty_id, status)
            VALUES (%s, %s, %s)
            ON CONFLICT (professor_id, faculty_id) DO UPDATE SET status = EXCLUDED.status
            RETURNING id
        """, (professor_id, faculty_id, status), fetch="one")

    @staticmethod
    def get_by_faculty(faculty_id):
        return execute_query("""
            SELECT pfa.*, p.name AS professor_name, p.email, p.phone, p.statut
            FROM professor_faculty_affiliations pfa
            JOIN professors p ON p.id = pfa.professor_id
            WHERE pfa.faculty_id = %s AND p.is_active = TRUE
            ORDER BY pfa.status, p.name
        """, (faculty_id,))

    @staticmethod
    def get_by_professor(professor_id):
        return execute_query("""
            SELECT pfa.*, f.name AS faculty_name
            FROM professor_faculty_affiliations pfa
            JOIN faculties f ON f.id = pfa.faculty_id
            WHERE pfa.professor_id = %s
            ORDER BY pfa.status, f.name
        """, (professor_id,))

    @staticmethod
    def update_status(professor_id, faculty_id, status):
        execute_query("""
            UPDATE professor_faculty_affiliations
            SET status = %s
            WHERE professor_id = %s AND faculty_id = %s
        """, (status, professor_id, faculty_id), fetch="none")

    @staticmethod
    def remove(professor_id, faculty_id):
        execute_query("""
            DELETE FROM professor_faculty_affiliations
            WHERE professor_id = %s AND faculty_id = %s
        """, (professor_id, faculty_id), fetch="none")


# ============================================================
# COURS
# ============================================================
class CourseQueries:

    @staticmethod
    def get_by_department(department_id):
        return execute_query("""
            SELECT c.*,
                   ue.name        AS ue_name,
                   ue.code        AS ue_code,
                   ue.group_label AS ue_group,
                   ue.credits     AS ue_credits,
                   p.name         AS professor_name,
                   pr.name        AS promotion_name
            FROM courses c
            LEFT JOIN unites_enseignement ue ON c.ue_id       = ue.id
            LEFT JOIN professors          p  ON c.professor_id = p.id
            LEFT JOIN promotions          pr ON c.promotion_id = pr.id
            WHERE c.department_id=%s AND c.is_active=TRUE
            ORDER BY pr.name NULLS LAST, ue.group_label NULLS LAST,
                     ue.name NULLS LAST, c.name
        """, (department_id,))

    @staticmethod
    def get_by_promotion(promotion_id):
        """Cours spécifiques à la promotion + cours partagés (sans promotion)."""
        return execute_query("""
            SELECT c.*,
                   ue.name        AS ue_name,
                   ue.code        AS ue_code,
                   ue.group_label AS ue_group,
                   ue.credits     AS ue_credits,
                   p.name         AS professor_name
            FROM courses c
            LEFT JOIN unites_enseignement ue ON c.ue_id       = ue.id
            LEFT JOIN professors          p  ON c.professor_id = p.id
            WHERE (c.promotion_id = %s OR c.promotion_id IS NULL)
              AND c.is_active = TRUE
            ORDER BY ue.group_label NULLS LAST, ue.name NULLS LAST, c.name
        """, (promotion_id,))

    @staticmethod
    def get_by_class(class_id):
        """
        Cours d'une classe : via les horaires en priorité, puis
        via la promotion de la classe, puis via le département.
        """
        courses = execute_query("""
            SELECT DISTINCT c.*,
                   ue.name AS ue_name, ue.code AS ue_code,
                   ue.group_label AS ue_group,
                   p.name AS professor_name
            FROM courses c
            LEFT JOIN unites_enseignement ue ON c.ue_id       = ue.id
            LEFT JOIN professors          p  ON c.professor_id = p.id
            JOIN schedules s ON s.course_id=c.id
            WHERE s.class_id=%s AND s.is_active=TRUE AND c.is_active=TRUE
            ORDER BY c.name
        """, (class_id,))
        if not courses:
            # Fallback 1 : cours de la promotion
            courses = execute_query("""
                SELECT c.*,
                       ue.name AS ue_name, ue.code AS ue_code,
                       ue.group_label AS ue_group,
                       p.name AS professor_name
                FROM courses c
                LEFT JOIN unites_enseignement ue ON c.ue_id       = ue.id
                LEFT JOIN professors          p  ON c.professor_id = p.id
                JOIN classes cl ON cl.id = %s
                WHERE c.promotion_id = cl.promotion_id AND c.is_active=TRUE
                ORDER BY c.name
            """, (class_id,))
        if not courses:
            # Fallback 2 : tous les cours du département
            courses = execute_query("""
                SELECT c.*,
                       ue.name AS ue_name, ue.code AS ue_code,
                       ue.group_label AS ue_group,
                       p.name AS professor_name
                FROM courses c
                LEFT JOIN unites_enseignement ue ON c.ue_id       = ue.id
                LEFT JOIN professors          p  ON c.professor_id = p.id
                JOIN departments d ON c.department_id=d.id
                JOIN promotions pr ON pr.department_id=d.id
                JOIN classes cl    ON cl.promotion_id=pr.id
                WHERE cl.id=%s AND c.is_active=TRUE
                ORDER BY c.name
            """, (class_id,))
        return courses or []

    @staticmethod
    def generate_code(department_id, name=""):
        """Génère le prochain code unique : initiales du nom + séquence (ex: MAT001)."""
        import re as _re
        words = [w for w in _re.sub(r'[^a-zA-ZÀ-ɏ]', ' ',
                                     name).upper().split() if len(w) > 1]
        if len(words) >= 2:
            prefix = "".join(w[0] for w in words[:3])
        elif words:
            prefix = words[0][:3]
        else:
            prefix = "EC"
        prefix = prefix[:3].upper()

        seq = execute_query(
            "SELECT COUNT(*) AS n FROM courses WHERE department_id=%s",
            (department_id,), fetch="one"
        )
        seq_n = (seq["n"] if seq else 0) + 1

        for _ in range(200):
            candidate = f"{prefix}{seq_n:03d}"
            taken = execute_query(
                "SELECT id FROM courses WHERE code=%s", (candidate,), fetch="one"
            )
            if not taken:
                return candidate
            seq_n += 1
        return f"{prefix}{seq_n:03d}"

    @staticmethod
    def get_by_id(course_id):
        return execute_query(
            "SELECT * FROM courses WHERE id=%s",
            (course_id,), fetch="one"
        )

    @staticmethod
    def create(name, code, hours, weight, department_id,
               promotion_id=None, professor_id=None):
        return execute_query(
            """INSERT INTO courses
               (name,code,hours,weight,department_id,promotion_id,professor_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (name, code or None, hours, weight, department_id,
             promotion_id, professor_id), fetch="one"
        )

    @staticmethod
    def update(course_id, name, code, hours, weight,
               promotion_id=None, professor_id=None):
        execute_query(
            """UPDATE courses SET name=%s,code=%s,hours=%s,weight=%s,
               promotion_id=%s,professor_id=%s WHERE id=%s""",
            (name, code or None, hours, weight,
             promotion_id, professor_id, course_id), fetch="none"
        )

    @staticmethod
    def delete(course_id):
        execute_query("UPDATE courses SET is_active=FALSE WHERE id=%s",
                      (course_id,), fetch="none")


# ============================================================
# SALLES PHYSIQUES
# ============================================================
class RoomQueries:

    TYPES = ["salle", "amphi", "labo", "salle_tp", "salle_info", "autre"]
    TYPE_LABELS = {
        "salle":      "Salle de cours",
        "amphi":      "Amphithéâtre",
        "labo":       "Laboratoire",
        "salle_tp":   "Salle TP",
        "salle_info": "Salle informatique",
        "autre":      "Autre",
    }

    @staticmethod
    def get_by_university(university_id):
        return execute_query("""
            SELECT r.*,
                   d.name AS department_name
            FROM rooms r
            LEFT JOIN departments d ON r.department_id = d.id
            WHERE r.university_id = %s AND r.is_active = TRUE
            ORDER BY r.building NULLS LAST, r.floor NULLS LAST, r.name
        """, (university_id,))

    @staticmethod
    def get_by_department(department_id):
        return execute_query("""
            SELECT r.*,
                   d.name AS department_name
            FROM rooms r
            LEFT JOIN departments d ON r.department_id = d.id
            JOIN departments dep ON dep.id = %s
            JOIN faculties   fac ON fac.id = dep.faculty_id
            WHERE r.university_id = fac.university_id AND r.is_active = TRUE
            ORDER BY r.building NULLS LAST, r.floor NULLS LAST, r.name
        """, (department_id,))

    @staticmethod
    def get_by_id(room_id):
        return execute_query(
            "SELECT * FROM rooms WHERE id = %s",
            (room_id,), fetch="one"
        )

    @staticmethod
    def create(name, code, capacity, room_type, building, floor,
               university_id, department_id=None):
        return execute_query("""
            INSERT INTO rooms
                (name, code, capacity, room_type, building, floor,
                 university_id, department_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (name, code or None, capacity or 0, room_type or "salle",
              building or None, floor or None,
              university_id, department_id), fetch="one")

    @staticmethod
    def update(room_id, name, code, capacity, room_type, building, floor,
               department_id=None):
        execute_query("""
            UPDATE rooms
            SET name=%s, code=%s, capacity=%s, room_type=%s,
                building=%s, floor=%s, department_id=%s
            WHERE id=%s
        """, (name, code or None, capacity or 0, room_type or "salle",
              building or None, floor or None,
              department_id, room_id), fetch="none")

    @staticmethod
    def delete(room_id):
        execute_query(
            "UPDATE rooms SET is_active=FALSE WHERE id=%s",
            (room_id,), fetch="none"
        )

    @staticmethod
    def check_availability(room_id, day, start_time, end_time,
                           exclude_schedule_id=None):
        """Retourne la liste des conflits pour cette salle sur ce créneau."""
        sql = """
            SELECT s.id, s.day, s.start_time, s.end_time,
                   c.name AS course_name,
                   cl.name AS class_name
            FROM schedules s
            LEFT JOIN courses c  ON s.course_id = c.id
            LEFT JOIN classes cl ON s.class_id  = cl.id
            WHERE s.room_id    = %s
              AND s.day        = %s
              AND s.is_active  = TRUE
              AND s.start_time < %s
              AND s.end_time   > %s
        """
        params = [room_id, day, end_time, start_time]
        if exclude_schedule_id:
            sql += " AND s.id != %s"
            params.append(exclude_schedule_id)
        return execute_query(sql, params)


# ============================================================
# EMPLOIS DU TEMPS
# ============================================================
class ScheduleQueries:

    @staticmethod
    def get_by_class(class_id):
        return execute_query("""
            SELECT s.*,
                   COALESCE(c.name, s.slot_label, 'Jour Férié') AS course_name,
                   c.code AS course_code,
                   COALESCE(p.name, '')                          AS professor_name,
                   cl.name AS class_name,
                   sp.name                                       AS substitute_name,
                   r.name  AS room_name,
                   r.code  AS room_code,
                   r.capacity AS room_capacity
            FROM schedules s
            LEFT JOIN courses    c  ON s.course_id=c.id
            LEFT JOIN professors p  ON s.professor_id=p.id
            LEFT JOIN professors sp ON s.substitute_professor_id=sp.id
            LEFT JOIN rooms      r  ON s.room_id=r.id
            JOIN      classes    cl ON s.class_id=cl.id
            WHERE s.class_id=%s AND s.is_active=TRUE
            ORDER BY
                CASE s.day
                    WHEN 'Lundi'    THEN 1 WHEN 'Mardi'   THEN 2
                    WHEN 'Mercredi' THEN 3 WHEN 'Jeudi'   THEN 4
                    WHEN 'Vendredi' THEN 5 WHEN 'Samedi'  THEN 6
                END, s.start_time
        """, (class_id,))

    @staticmethod
    def get_by_professor(professor_id):
        """Tous les créneaux du professeur avec cours, classe, promotion, dept, faculté, salle."""
        return execute_query("""
            SELECT s.*,
                   COALESCE(c.name, s.slot_label, 'Événement') AS course_name,
                   c.code          AS course_code,
                   cl.name         AS class_name,
                   pr.name         AS promotion_name,
                   pr.academic_year,
                   d.name          AS department_name,
                   f.name          AS faculty_name,
                   COALESCE(r.name, s.room) AS room_name,
                   r.code          AS room_code,
                   r.capacity      AS room_capacity
            FROM schedules s
            LEFT JOIN courses    c  ON s.course_id    = c.id
            JOIN      classes    cl ON s.class_id     = cl.id
            JOIN      promotions pr ON cl.promotion_id = pr.id
            JOIN      departments d ON pr.department_id = d.id
            JOIN      faculties   f ON d.faculty_id    = f.id
            LEFT JOIN rooms       r ON s.room_id       = r.id
            WHERE s.professor_id = %s
              AND s.is_active = TRUE
              AND (s.valid_from  IS NULL OR s.valid_from  <= CURRENT_DATE)
              AND (s.valid_until IS NULL OR s.valid_until >= CURRENT_DATE)
            ORDER BY
                CASE s.day
                    WHEN 'Lundi'    THEN 1 WHEN 'Mardi'    THEN 2
                    WHEN 'Mercredi' THEN 3 WHEN 'Jeudi'    THEN 4
                    WHEN 'Vendredi' THEN 5 WHEN 'Samedi'   THEN 6
                END,
                s.start_time
        """, (professor_id,))

    @staticmethod
    def check_conflict(class_id, day, start_time, end_time, exclude_id=None):
        sql = """
            SELECT id FROM schedules
            WHERE class_id=%s AND day=%s AND is_active=TRUE
            AND NOT (end_time <= %s::time OR start_time >= %s::time)
        """
        params = [class_id, day, start_time, end_time]
        if exclude_id:
            sql += " AND id != %s"
            params.append(exclude_id)
        return execute_query(sql, params)

    @staticmethod
    def create(class_id, day, start_time, end_time, room, course_id, professor_id,
               week_type="Toutes", valid_from=None, valid_until=None,
               slot_type="cours", slot_label=None, room_id=None):
        return execute_query("""
            INSERT INTO schedules
                (class_id,day,start_time,end_time,room,course_id,professor_id,
                 week_type,valid_from,valid_until,slot_type,slot_label,room_id)
            VALUES (%s,%s,%s::time,%s::time,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (class_id, day, start_time, end_time, room or None,
              course_id or None, professor_id or None, week_type,
              valid_from or None, valid_until or None,
              slot_type or "cours", slot_label or None, room_id), fetch="one")

    @staticmethod
    def update(schedule_id, day, start_time, end_time, room, course_id, professor_id,
               week_type, valid_from=None, valid_until=None,
               slot_type="cours", slot_label=None, room_id=None):
        execute_query("""
            UPDATE schedules SET day=%s,start_time=%s::time,end_time=%s::time,
            room=%s,course_id=%s,professor_id=%s,week_type=%s,
            valid_from=%s,valid_until=%s,slot_type=%s,slot_label=%s,room_id=%s
            WHERE id=%s
        """, (day, start_time, end_time, room or None,
              course_id or None, professor_id or None, week_type,
              valid_from or None, valid_until or None,
              slot_type or "cours", slot_label or None,
              room_id, schedule_id), fetch="none")

    @staticmethod
    def delete(schedule_id):
        execute_query("UPDATE schedules SET is_active=FALSE WHERE id=%s",
                      (schedule_id,), fetch="none")

    @staticmethod
    def check_professor_conflict(professor_id, day, start_time, end_time, exclude_id=None):
        """Verifie si le prof est deja occupe dans une autre classe au meme creneau."""
        sql = """
            SELECT s.id, cl.name AS class_name FROM schedules s
            JOIN classes cl ON s.class_id=cl.id
            WHERE s.professor_id=%s AND s.day=%s AND s.is_active=TRUE
            AND s.slot_type='cours'
            AND NOT (s.end_time <= %s::time OR s.start_time >= %s::time)
        """
        params = [professor_id, day, start_time, end_time]
        if exclude_id:
            sql += " AND s.id != %s"
            params.append(exclude_id)
        return execute_query(sql, params)

    @staticmethod
    def check_room_conflict(room, day, start_time, end_time, exclude_id=None):
        """Verifie si la salle est deja utilisee au meme creneau."""
        if not room or not room.strip():
            return []
        sql = """
            SELECT s.id, cl.name AS class_name FROM schedules s
            JOIN classes cl ON s.class_id=cl.id
            WHERE LOWER(s.room)=LOWER(%s) AND s.day=%s AND s.is_active=TRUE
            AND NOT (s.end_time <= %s::time OR s.start_time >= %s::time)
        """
        params = [room.strip(), day, start_time, end_time]
        if exclude_id:
            sql += " AND s.id != %s"
            params.append(exclude_id)
        return execute_query(sql, params)

    @staticmethod
    def duplicate_schedules(source_class_id, target_class_id):
        """Copie tous les creneaux actifs d'une classe vers une autre."""
        rows = execute_query(
            "SELECT * FROM schedules WHERE class_id=%s AND is_active=TRUE",
            (source_class_id,)
        )
        created = 0
        for r in rows:
            execute_query("""
                INSERT INTO schedules
                    (class_id,day,start_time,end_time,room,course_id,professor_id,
                     week_type,valid_from,valid_until,slot_type,slot_label)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (target_class_id, r['day'], r['start_time'], r['end_time'],
                  r.get('room'), r.get('course_id'), r.get('professor_id'),
                  r.get('week_type', 'Toutes'), r.get('valid_from'), r.get('valid_until'),
                  r.get('slot_type', 'cours'), r.get('slot_label')), fetch="none")
            created += 1
        return created

    @staticmethod
    def set_status(schedule_id, status, note=None, substitute_id=None, changed_by=None):
        """Annule ou marque un remplacement sur un creneau."""
        execute_query("""
            UPDATE schedules SET slot_status=%s, cancel_note=%s,
            substitute_professor_id=%s WHERE id=%s
        """, (status, note or None, substitute_id or None, schedule_id), fetch="none")
        _note_safe = (note or "").replace('"', '\\"')
        execute_query("""
            INSERT INTO schedule_audit(schedule_id,action,changed_by,new_values)
            VALUES (%s,%s,%s,%s::jsonb)
        """, (schedule_id, status, changed_by or 'admin',
              f'{{"status":"{status}","note":"{_note_safe}"}}'), fetch="none")

    @staticmethod
    def get_audit(schedule_id):
        return execute_query("""
            SELECT * FROM schedule_audit WHERE schedule_id=%s ORDER BY changed_at DESC LIMIT 20
        """, (schedule_id,))

    @staticmethod
    def get_stats(department_id):
        return execute_query("""
            SELECT
                COUNT(DISTINCT s.id)                        AS total_slots,
                COUNT(DISTINCT s.professor_id)              AS total_profs,
                COUNT(DISTINCT s.course_id)                 AS total_courses,
                COUNT(DISTINCT s.class_id)                  AS total_classes,
                COUNT(DISTINCT CASE WHEN s.slot_type='examen' THEN s.id END) AS total_exams,
                SUM(EXTRACT(EPOCH FROM (s.end_time - s.start_time))/3600)    AS total_hours,
                COUNT(DISTINCT CASE WHEN s.slot_status='annule' THEN s.id END) AS cancelled
            FROM schedules s
            JOIN classes cl ON s.class_id=cl.id
            JOIN promotions pr ON cl.promotion_id=pr.id
            WHERE pr.department_id=%s AND s.is_active=TRUE
        """, (department_id,), fetch="one")

    @staticmethod
    def get_professor_hours(department_id):
        return execute_query("""
            SELECT p.name, p.email,
                   COUNT(DISTINCT s.id) AS nb_slots,
                   ROUND(SUM(EXTRACT(EPOCH FROM (s.end_time-s.start_time))/3600)::numeric,1) AS total_hours
            FROM schedules s
            JOIN professors p ON s.professor_id=p.id
            JOIN classes cl ON s.class_id=cl.id
            JOIN promotions pr ON cl.promotion_id=pr.id
            WHERE pr.department_id=%s AND s.is_active=TRUE AND s.slot_type='cours'
            GROUP BY p.id, p.name, p.email
            ORDER BY total_hours DESC
        """, (department_id,))

    @staticmethod
    def get_room_usage(department_id):
        return execute_query("""
            SELECT s.room,
                   COUNT(DISTINCT s.id) AS nb_slots,
                   ROUND(SUM(EXTRACT(EPOCH FROM (s.end_time-s.start_time))/3600)::numeric,1) AS total_hours
            FROM schedules s
            JOIN classes cl ON s.class_id=cl.id
            JOIN promotions pr ON cl.promotion_id=pr.id
            WHERE pr.department_id=%s AND s.is_active=TRUE AND s.room IS NOT NULL AND s.room != ''
            GROUP BY s.room
            ORDER BY total_hours DESC
        """, (department_id,))


# ============================================================
# COMMUNIQUÉS
# ============================================================
class AnnouncementQueries:

    @staticmethod
    def get_by_department(department_id, limit=20):
        return execute_query("""
            SELECT * FROM announcements
            WHERE department_id=%s
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY is_pinned DESC, created_at DESC
            LIMIT %s
        """, (department_id, limit))

    @staticmethod
    def get_by_university(university_id, limit=30):
        return execute_query("""
            SELECT a.*, u.name AS author_name
            FROM announcements a
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.university_id = %s
            AND (a.expires_at IS NULL OR a.expires_at > NOW())
            ORDER BY a.is_pinned DESC, a.created_at DESC
            LIMIT %s
        """, (university_id, limit))

    @staticmethod
    def get_by_class(class_id):
        return execute_query("""
            SELECT DISTINCT a.* FROM announcements a
            JOIN departments d  ON a.department_id=d.id
            JOIN promotions  pr ON pr.department_id=d.id
            JOIN classes     cl ON cl.promotion_id=pr.id
            WHERE cl.id=%s
            AND (a.expires_at IS NULL OR a.expires_at > NOW())
            ORDER BY a.is_pinned DESC, a.created_at DESC
            LIMIT 20
        """, (class_id,))

    @staticmethod
    def create(title, content, department_id=None, is_pinned=False, expires_at=None,
               file_url=None, file_name=None, university_id=None, created_by=None):
        return execute_query("""
            INSERT INTO announcements
                (title, content, department_id, is_pinned, expires_at,
                 file_url, file_name, university_id, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (title, content, department_id, is_pinned, expires_at,
              file_url, file_name, university_id, created_by), fetch="one")

    @staticmethod
    def update(announcement_id, title, content, is_pinned):
        execute_query(
            "UPDATE announcements SET title=%s,content=%s,is_pinned=%s WHERE id=%s",
            (title, content, is_pinned, announcement_id), fetch="none"
        )

    @staticmethod
    def delete(announcement_id):
        execute_query("DELETE FROM announcements WHERE id=%s",
                      (announcement_id,), fetch="none")


# ============================================================
# UTILISATEURS / AUTH
# ============================================================
class UserQueries:

    @staticmethod
    def get_by_email(email):
        return execute_query(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(%s) AND is_active=TRUE",
            (email,), fetch="one"
        )

    @staticmethod
    def get_by_id(user_id):
        return execute_query("SELECT * FROM users WHERE id=%s",
                             (user_id,), fetch="one")

    @staticmethod
    def create(name, email, password_hash, role,
               university_id=None, faculty_id=None, department_id=None):
        return execute_query("""
            INSERT INTO users (name,email,password_hash,role,university_id,faculty_id,department_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (name, email, password_hash, role,
              university_id, faculty_id, department_id), fetch="one")

    @staticmethod
    def update_last_login(user_id):
        execute_query("UPDATE users SET last_login=NOW() WHERE id=%s",
                      (user_id,), fetch="none")

    @staticmethod
    def get_admins_by_university(university_id):
        return execute_query(
            "SELECT id,name,email,role,is_active,created_at FROM users "
            "WHERE university_id=%s ORDER BY name",
            (university_id,)
        )

    @staticmethod
    def deactivate(user_id):
        execute_query("UPDATE users SET is_active=FALSE WHERE id=%s",
                      (user_id,), fetch="none")

    @staticmethod
    def update_password(user_id, password_hash):
        execute_query("UPDATE users SET password_hash=%s WHERE id=%s",
                      (password_hash, user_id), fetch="none")

    @staticmethod
    def create_professor_account(name, email, password_hash,
                                 university_id, faculty_id, department_id, professor_id):
        return execute_query("""
            INSERT INTO users
                (name, email, password_hash, role,
                 university_id, faculty_id, department_id, professor_id)
            VALUES (%s, %s, %s, 'professeur', %s, %s, %s, %s) RETURNING id
        """, (name, email, password_hash,
              university_id, faculty_id, department_id, professor_id), fetch="one")

    @staticmethod
    def get_professor_account(professor_id):
        return execute_query(
            "SELECT * FROM users WHERE professor_id=%s AND role='professeur'",
            (professor_id,), fetch="one"
        )


# ============================================================
# PROFESSEURS — méthodes supplémentaires
# ============================================================
class ProfessorExtQueries:

    @staticmethod
    def get_with_account(department_id):
        """Professeurs affiliés à la faculté de ce département, avec info compte."""
        return execute_query("""
            SELECT DISTINCT p.*,
                   pfa.status  AS affiliation_status,
                   u.id        AS user_id,
                   u.email     AS account_email,
                   u.is_active AS account_active
            FROM professors p
            JOIN professor_faculty_affiliations pfa ON pfa.professor_id = p.id
            JOIN departments d ON d.faculty_id = pfa.faculty_id
            LEFT JOIN users u ON u.professor_id = p.id AND u.role = 'professeur'
            WHERE d.id = %s AND p.is_active = TRUE
            ORDER BY p.name
        """, (department_id,))

    @staticmethod
    def get_classes(professor_id):
        """Classes où ce prof a au moins un créneau."""
        return execute_query("""
            SELECT DISTINCT cl.*,
                   pr.name       AS promotion_name,
                   pr.academic_year,
                   d.name        AS department_name
            FROM classes cl
            JOIN promotions pr ON cl.promotion_id = pr.id
            JOIN departments d ON pr.department_id = d.id
            JOIN schedules   s ON s.class_id = cl.id
            WHERE s.professor_id = %s AND s.is_active = TRUE AND cl.is_active = TRUE
            ORDER BY cl.name
        """, (professor_id,))

    @staticmethod
    def get_courses(professor_id):
        """Cours enseignés par ce prof (via professor_id direct ou via les horaires)."""
        return execute_query("""
            SELECT DISTINCT c.*,
                   pr.name AS promotion_name,
                   ue.name AS ue_name, ue.code AS ue_code
            FROM courses c
            LEFT JOIN promotions pr ON c.promotion_id = pr.id
            LEFT JOIN unites_enseignement ue ON c.ue_id = ue.id
            WHERE c.is_active = TRUE
              AND (
                c.professor_id = %s
                OR c.id IN (
                    SELECT course_id FROM schedules
                    WHERE professor_id = %s AND is_active = TRUE
                )
              )
            ORDER BY pr.name NULLS LAST, c.name
        """, (professor_id, professor_id))

    @staticmethod
    def get_promotions(professor_id):
        """Promotions où ce prof enseigne (via les horaires)."""
        return execute_query("""
            SELECT DISTINCT pr.*
            FROM promotions pr
            JOIN classes    cl ON cl.promotion_id = pr.id
            JOIN schedules  s  ON s.class_id      = cl.id
            WHERE s.professor_id = %s AND s.is_active = TRUE AND pr.is_active = TRUE
            ORDER BY pr.name
        """, (professor_id,))

    @staticmethod
    def get_courses_by_department(professor_id, department_id):
        """Tous les cours du département (pour upload de documents)."""
        return execute_query(
            "SELECT * FROM courses WHERE department_id=%s AND is_active=TRUE ORDER BY name",
            (department_id,)
        )

    @staticmethod
    def get_faculties_for_prof(professor_id):
        """Facultés où ce professeur enseigne (via horaires ou affectation directe)."""
        return execute_query("""
            SELECT DISTINCT f.id, f.name
            FROM faculties f
            WHERE f.is_active = TRUE
              AND (
                EXISTS (
                    SELECT 1 FROM departments d
                    JOIN promotions pr ON pr.department_id = d.id
                    JOIN classes cl ON cl.promotion_id = pr.id
                    JOIN schedules s ON s.class_id = cl.id
                    WHERE d.faculty_id = f.id
                      AND s.professor_id = %s AND s.is_active = TRUE
                )
                OR EXISTS (
                    SELECT 1 FROM departments d
                    JOIN courses c ON c.department_id = d.id
                    WHERE d.faculty_id = f.id
                      AND c.professor_id = %s AND c.is_active = TRUE
                )
              )
            ORDER BY f.name
        """, (professor_id, professor_id))

    @staticmethod
    def get_departments_for_prof(professor_id, faculty_id):
        """Départements d'une faculté où ce professeur enseigne."""
        return execute_query("""
            SELECT DISTINCT d.id, d.name
            FROM departments d
            WHERE d.faculty_id = %s
              AND (
                EXISTS (
                    SELECT 1 FROM promotions pr
                    JOIN classes cl ON cl.promotion_id = pr.id
                    JOIN schedules s ON s.class_id = cl.id
                    WHERE pr.department_id = d.id
                      AND s.professor_id = %s AND s.is_active = TRUE
                )
                OR EXISTS (
                    SELECT 1 FROM courses c
                    WHERE c.department_id = d.id
                      AND c.professor_id = %s AND c.is_active = TRUE
                )
              )
            ORDER BY d.name
        """, (faculty_id, professor_id, professor_id))

    @staticmethod
    def get_promotions_for_prof(professor_id, department_id):
        """Promotions d'un département où ce professeur enseigne."""
        return execute_query("""
            SELECT DISTINCT pr.id, pr.name, pr.academic_year
            FROM promotions pr
            WHERE pr.department_id = %s AND pr.is_active = TRUE
              AND (
                EXISTS (
                    SELECT 1 FROM classes cl
                    JOIN schedules s ON s.class_id = cl.id
                    WHERE cl.promotion_id = pr.id
                      AND s.professor_id = %s AND s.is_active = TRUE
                )
                OR EXISTS (
                    SELECT 1 FROM courses c
                    WHERE c.promotion_id = pr.id
                      AND c.professor_id = %s AND c.is_active = TRUE
                )
              )
            ORDER BY pr.name
        """, (department_id, professor_id, professor_id))

    @staticmethod
    def get_courses_for_prof(professor_id, promotion_id):
        """Cours enseignés par ce professeur dans une promotion donnée."""
        return execute_query("""
            SELECT DISTINCT c.id, c.name, c.code
            FROM courses c
            WHERE c.promotion_id = %s AND c.is_active = TRUE
              AND (
                c.professor_id = %s
                OR c.id IN (
                    SELECT course_id FROM schedules
                    WHERE professor_id = %s AND is_active = TRUE
                )
              )
            ORDER BY c.name
        """, (promotion_id, professor_id, professor_id))


# ============================================================
# REGISTRE ÉTUDIANTS
# ============================================================
class StudentRegistryQueries:

    @staticmethod
    def get_by_university(university_id):
        return execute_query("""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name,
                   (s.id IS NOT NULL)  AS is_registered,
                   s.id                AS student_account_id,
                   s.username          AS student_username,
                   s.is_active         AS student_is_active
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            LEFT JOIN students      s  ON s.registry_id   = r.id
            WHERE r.university_id=%s
            ORDER BY r.annee_academique DESC NULLS LAST,
                     d.name NULLS LAST,
                     fi.name NULLS LAST,
                     o.name NULLS LAST,
                     r.full_name
        """, (university_id,))

    @staticmethod
    def get_stats(university_id):
        """Statistiques légères sans charger tous les enregistrements."""
        return execute_query("""
            SELECT
                COUNT(*)                              AS total,
                COUNT(s.id)                           AS registered,
                COUNT(*) - COUNT(s.id)                AS pending
            FROM student_registry r
            LEFT JOIN students s ON s.registry_id = r.id
            WHERE r.university_id = %s
        """, (university_id,), fetch="one")

    @staticmethod
    def _build_filter_clause(annee=None, filiere_id=None, option_id=None,
                             promotion_id=None, search=None, compte_filter=None):
        """Construit WHERE + params pour les filtres courants."""
        clauses, params = [], []
        if annee:
            clauses.append("r.annee_academique = %s"); params.append(annee)
        if filiere_id:
            clauses.append("r.filiere_id = %s"); params.append(filiere_id)
        if option_id:
            clauses.append("r.option_id = %s"); params.append(option_id)
        if promotion_id:
            clauses.append("r.promotion_id = %s"); params.append(promotion_id)
        if search:
            clauses.append(
                "(r.student_number ILIKE %s OR r.full_name ILIKE %s "
                " OR r.nom ILIKE %s OR r.prenom ILIKE %s)"
            )
            like = f"%{search}%"
            params += [like, like, like, like]
        if compte_filter == "avec":
            clauses.append("s.id IS NOT NULL")
        elif compte_filter == "sans":
            clauses.append("s.id IS NULL")
        return clauses, params

    @staticmethod
    def count_filtered(university_id, annee=None, filiere_id=None,
                       option_id=None, promotion_id=None,
                       search=None, compte_filter=None):
        """Nombre total de lignes après filtres (pour pagination)."""
        clauses, params = StudentRegistryQueries._build_filter_clause(
            annee, filiere_id, option_id, promotion_id, search, compte_filter
        )
        where = "WHERE r.university_id=%s"
        params = [university_id] + params
        if clauses:
            where += " AND " + " AND ".join(clauses)
        row = execute_query(f"""
            SELECT COUNT(*) AS n
            FROM student_registry r
            LEFT JOIN students s ON s.registry_id = r.id
            {where}
        """, params, fetch="one")
        return row["n"] if row else 0

    @staticmethod
    def get_paginated(university_id, page=1, per_page=50,
                      annee=None, filiere_id=None, option_id=None,
                      promotion_id=None, search=None, compte_filter=None):
        """Retourne une page d'étudiants avec filtres côté serveur."""
        clauses, params = StudentRegistryQueries._build_filter_clause(
            annee, filiere_id, option_id, promotion_id, search, compte_filter
        )
        where = "WHERE r.university_id=%s"
        params = [university_id] + params
        if clauses:
            where += " AND " + " AND ".join(clauses)
        offset = (page - 1) * per_page
        params += [per_page, offset]
        return execute_query(f"""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name,
                   (s.id IS NOT NULL) AS is_registered,
                   s.id               AS student_account_id,
                   s.username         AS student_username,
                   s.is_active        AS student_is_active
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            LEFT JOIN students      s  ON s.registry_id   = r.id
            {where}
            ORDER BY r.annee_academique DESC NULLS LAST,
                     d.name NULLS LAST, fi.name NULLS LAST, r.full_name
            LIMIT %s OFFSET %s
        """, params)

    @staticmethod
    def get_all_filtered(university_id, annee=None, filiere_id=None,
                         option_id=None, promotion_id=None,
                         search=None, compte_filter=None, limit=5000):
        """Pour export — retourne tous les résultats filtrés (plafonné à limit)."""
        clauses, params = StudentRegistryQueries._build_filter_clause(
            annee, filiere_id, option_id, promotion_id, search, compte_filter
        )
        where = "WHERE r.university_id=%s"
        params = [university_id] + params
        if clauses:
            where += " AND " + " AND ".join(clauses)
        params.append(limit)
        return execute_query(f"""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name,
                   (s.id IS NOT NULL) AS is_registered,
                   s.id               AS student_account_id,
                   s.username         AS student_username,
                   s.is_active        AS student_is_active
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            LEFT JOIN students      s  ON s.registry_id   = r.id
            {where}
            ORDER BY r.annee_academique DESC NULLS LAST,
                     d.name NULLS LAST, fi.name NULLS LAST, r.full_name
            LIMIT %s
        """, params)

    @staticmethod
    def get_by_department(department_id):
        return execute_query("""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name,
                   (s.id IS NOT NULL)  AS is_registered,
                   s.id                AS student_account_id,
                   s.username          AS student_username,
                   s.is_active         AS student_is_active
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            LEFT JOIN students      s  ON s.registry_id   = r.id
            WHERE r.department_id=%s
            ORDER BY r.annee_academique DESC NULLS LAST,
                     fi.name NULLS LAST, o.name NULLS LAST, r.full_name
        """, (department_id,))

    @staticmethod
    def get_by_faculty(faculty_id):
        return execute_query("""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name,
                   (s.id IS NOT NULL)  AS is_registered,
                   s.username          AS student_username
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            LEFT JOIN students      s  ON s.registry_id   = r.id
            WHERE d.faculty_id = %s
            ORDER BY r.annee_academique DESC NULLS LAST,
                     d.name NULLS LAST, fi.name NULLS LAST, r.full_name
        """, (faculty_id,))

    @staticmethod
    def get_by_filiere(filiere_id, annee_academique=None):
        sql = """
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            WHERE r.filiere_id=%s
        """
        params = [filiere_id]
        if annee_academique:
            sql += " AND r.annee_academique=%s"
            params.append(annee_academique)
        sql += " ORDER BY o.name NULLS LAST, pr.name NULLS LAST, r.full_name"
        return execute_query(sql, params)

    @staticmethod
    def get_by_option(option_id, annee_academique=None):
        sql = """
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            WHERE r.option_id=%s
        """
        params = [option_id]
        if annee_academique:
            sql += " AND r.annee_academique=%s"
            params.append(annee_academique)
        sql += " ORDER BY pr.name NULLS LAST, r.full_name"
        return execute_query(sql, params)

    @staticmethod
    def get_by_promotion_id(promotion_id, annee_academique=None):
        sql = """
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            WHERE r.promotion_id=%s
        """
        params = [promotion_id]
        if annee_academique:
            sql += " AND r.annee_academique=%s"
            params.append(annee_academique)
        sql += " ORDER BY r.full_name"
        return execute_query(sql, params)

    @staticmethod
    def get_by_id(registry_id):
        return execute_query("""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            WHERE r.id=%s
        """, (registry_id,), fetch="one")

    @staticmethod
    def verify(student_number, university_id):
        """Vérifie si le numéro étudiant existe dans la liste d'inscription."""
        return execute_query("""
            SELECT r.*,
                   d.name  AS department_name,
                   fi.name AS filiere_name,
                   o.name  AS option_name,
                   pr.name AS promotion_name
            FROM student_registry r
            LEFT JOIN departments   d  ON r.department_id = d.id
            LEFT JOIN filieres      fi ON r.filiere_id    = fi.id
            LEFT JOIN options_etude o  ON r.option_id     = o.id
            LEFT JOIN promotions    pr ON r.promotion_id  = pr.id
            WHERE r.student_number=%s AND r.university_id=%s
        """, (student_number.strip().upper(), university_id), fetch="one")

    @staticmethod
    def mark_registered(registry_id):
        execute_query(
            "UPDATE student_registry SET is_registered=TRUE WHERE id=%s",
            (registry_id,), fetch="none"
        )

    @staticmethod
    def create(student_number, full_name, university_id, class_id=None):
        return execute_query("""
            INSERT INTO student_registry (student_number, full_name, university_id, class_id)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (student_number.strip().upper(), full_name.strip(),
              university_id, class_id), fetch="one")

    @staticmethod
    def create_full(student_number, full_name, university_id, class_id=None,
                    nom=None, postnom=None, prenom=None,
                    promotion_txt=None, option_txt=None,
                    department_id=None, filiere_id=None, option_id=None,
                    promotion_id=None, annee_academique=None,
                    provenance=None, date_naissance=None, sexe=None):
        return execute_query("""
            INSERT INTO student_registry
                (student_number, full_name, university_id, class_id,
                 nom, postnom, prenom, promotion_txt, option_txt,
                 department_id, filiere_id, option_id, promotion_id,
                 annee_academique, provenance, date_naissance, sexe)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (student_number.strip().upper(), full_name.strip(),
              university_id, class_id,
              nom, postnom, prenom, promotion_txt, option_txt,
              department_id, filiere_id, option_id, promotion_id,
              annee_academique, provenance, date_naissance, sexe),
                             fetch="one")

    @staticmethod
    def delete(registry_id):
        # Délier + supprimer en une seule transaction atomique (FK sans CASCADE)
        execute_query("""
            WITH _unlink AS (
                UPDATE students SET registry_id = NULL WHERE registry_id = %s
            )
            DELETE FROM student_registry WHERE id = %s
        """, (registry_id, registry_id), fetch="none")

    @staticmethod
    def update_statut(registry_id, statut):
        execute_query(
            "UPDATE student_registry SET statut=%s WHERE id=%s",
            (statut, registry_id), fetch="none"
        )

    @staticmethod
    def generate_from_previous_year(
        source_promotion_id, source_year,
        target_promotion_id, new_year,
        university_id
    ) -> dict:
        """
        Génère la liste d'inscrits pour new_year/target_promotion à partir de :
        - Les ADMIS de source_promotion/source_year (promus vers la promo suivante)
        - Les REDOUBLANTS de target_promotion/année précédente de new_year
        Retourne {"admis": n, "redoublants": n}.
        """
        # Calcul de l'année précédente (ex: "2025-2026" → "2024-2025")
        try:
            start = int(new_year.split("-")[0])
            prev_year = f"{start - 1}-{start}"
        except (ValueError, IndexError):
            prev_year = None

        # ── Admis (promus depuis la promotion source) ──────────────────────────
        r_admis = execute_query("""
            INSERT INTO student_registry
                (student_number, full_name, university_id, class_id,
                 nom, postnom, prenom, promotion_txt, option_txt,
                 department_id, filiere_id, option_id, promotion_id,
                 annee_academique, provenance, date_naissance, sexe, statut)
            SELECT
                r.student_number, r.full_name, r.university_id, NULL,
                r.nom, r.postnom, r.prenom, pr.name, r.option_txt,
                r.department_id, r.filiere_id, r.option_id, %s,
                %s, src_pr.name, r.date_naissance, r.sexe, 'inscrit'
            FROM student_registry r
            JOIN promotions pr ON pr.id = %s
            JOIN promotions src_pr ON src_pr.id = %s
            WHERE r.promotion_id = %s
              AND r.annee_academique = %s
              AND r.statut = 'admis'
              AND r.university_id = %s
            ON CONFLICT (student_number, university_id, annee_academique) DO NOTHING
            RETURNING id
        """, (target_promotion_id, new_year, target_promotion_id,
              source_promotion_id, source_promotion_id, source_year, university_id))

        # ── Redoublants (même promo, année précédente) ─────────────────────────
        r_redoub = []
        if prev_year:
            r_redoub = execute_query("""
                INSERT INTO student_registry
                    (student_number, full_name, university_id, class_id,
                     nom, postnom, prenom, promotion_txt, option_txt,
                     department_id, filiere_id, option_id, promotion_id,
                     annee_academique, provenance, date_naissance, sexe, statut)
                SELECT
                    r.student_number, r.full_name, r.university_id, NULL,
                    r.nom, r.postnom, r.prenom, r.promotion_txt, r.option_txt,
                    r.department_id, r.filiere_id, r.option_id, r.promotion_id,
                    %s, r.provenance, r.date_naissance, r.sexe, 'inscrit'
                FROM student_registry r
                WHERE r.promotion_id = %s
                  AND r.annee_academique = %s
                  AND r.statut = 'redoublant'
                  AND r.university_id = %s
                ON CONFLICT (student_number, university_id, annee_academique) DO NOTHING
                RETURNING id
            """, (new_year, target_promotion_id, prev_year, university_id))

        return {
            "admis":      len(r_admis or []),
            "redoublants": len(r_redoub or []),
        }

    @staticmethod
    def update_class(registry_id, class_id):
        execute_query(
            "UPDATE student_registry SET class_id=%s WHERE id=%s",
            (class_id, registry_id), fetch="none"
        )

    @staticmethod
    def get_annees_academiques(university_id):
        """Années académiques distinctes présentes dans le registre."""
        rows = execute_query("""
            SELECT DISTINCT annee_academique
            FROM student_registry
            WHERE university_id=%s AND annee_academique IS NOT NULL
            ORDER BY annee_academique DESC
        """, (university_id,))
        return [r["annee_academique"] for r in (rows or [])]


# ============================================================
# ÉTUDIANTS
# ============================================================
class StudentQueries:

    @staticmethod
    def get_by_credentials(student_number, university_id):
        return execute_query("""
            SELECT * FROM students
            WHERE student_number=%s AND university_id=%s AND is_active=TRUE
        """, (student_number.strip().upper(), university_id), fetch="one")

    @staticmethod
    def get_by_id(student_id):
        return execute_query(
            "SELECT * FROM students WHERE id=%s",
            (student_id,), fetch="one"
        )

    @staticmethod
    def get_by_class(class_id):
        return execute_query(
            "SELECT * FROM students WHERE class_id=%s AND is_active=TRUE ORDER BY full_name",
            (class_id,)
        )

    @staticmethod
    def create(student_number, full_name, email, password_hash,
               class_id, university_id, registry_id,
               nom=None, postnom=None, prenom=None, username=None):
        return execute_query("""
            INSERT INTO students
                (student_number, full_name, email, password_hash,
                 class_id, university_id, registry_id,
                 nom, postnom, prenom, username)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (student_number.strip().upper(), full_name.strip(),
              email.strip().lower() if email else None,
              password_hash, class_id, university_id, registry_id,
              nom, postnom, prenom,
              username.strip() if username else None), fetch="one")

    @staticmethod
    def set_active(student_id, is_active: bool):
        execute_query("UPDATE students SET is_active=%s WHERE id=%s",
                      (is_active, student_id), fetch="none")

    @staticmethod
    def get_by_department(department_id):
        """Tous les étudiants dont la promotion appartient à ce département."""
        return execute_query("""
            SELECT s.*, cl.name AS class_name, pr.name AS promotion_name
            FROM students s
            JOIN classes    cl ON s.class_id      = cl.id
            JOIN promotions pr ON cl.promotion_id = pr.id
            WHERE pr.department_id = %s
            ORDER BY pr.name, cl.name, s.full_name
        """, (department_id,))

    @staticmethod
    def reset_password(student_id, new_password_hash):
        execute_query("UPDATE students SET password_hash=%s WHERE id=%s",
                      (new_password_hash, student_id), fetch="none")

    @staticmethod
    def update_last_login(student_id):
        execute_query("UPDATE students SET last_login=NOW() WHERE id=%s",
                      (student_id,), fetch="none")

    @staticmethod
    def exists(student_number, university_id):
        return execute_query("""
            SELECT id FROM students
            WHERE student_number=%s AND university_id=%s
        """, (student_number.strip().upper(), university_id), fetch="one")

    @staticmethod
    def get_by_login(login_input, university_id):
        """Trouve un étudiant par numéro étudiant OU nom d'utilisateur (actif ou non)."""
        return execute_query("""
            SELECT * FROM students
            WHERE university_id=%s
              AND (student_number=%s OR username=%s)
        """, (university_id,
              login_input.strip().upper(),
              login_input.strip()), fetch="one")

    @staticmethod
    def exists_username(username):
        return execute_query(
            "SELECT id FROM students WHERE username=%s",
            (username.strip(),), fetch="one"
        )


# ============================================================
# DOCUMENTS DE COURS
# ============================================================
class CourseDocumentQueries:

    @staticmethod
    def get_by_course(course_id):
        return execute_query("""
            SELECT cd.*, p.name AS professor_name
            FROM course_documents cd
            JOIN professors p ON cd.professor_id = p.id
            WHERE cd.course_id=%s AND cd.is_active=TRUE
            ORDER BY cd.created_at DESC
        """, (course_id,))

    @staticmethod
    def get_by_professor(professor_id):
        return execute_query("""
            SELECT cd.*, c.name AS course_name, c.code AS course_code,
                   pr.name AS promotion_name
            FROM course_documents cd
            JOIN courses    c  ON cd.course_id    = c.id
            LEFT JOIN promotions pr ON cd.promotion_id = pr.id
            WHERE cd.professor_id=%s AND cd.is_active=TRUE
            ORDER BY cd.created_at DESC
        """, (professor_id,))

    @staticmethod
    def get_by_class(class_id):
        """Documents de la promotion de l'étudiant (classe → promotion)."""
        return execute_query("""
            SELECT cd.*, c.name AS course_name, p.name AS professor_name
            FROM course_documents cd
            JOIN courses    c  ON cd.course_id    = c.id
            JOIN professors p  ON cd.professor_id = p.id
            JOIN classes    cl ON cl.id           = %s
            WHERE cd.promotion_id = cl.promotion_id
              AND cd.is_active = TRUE
            ORDER BY c.name, cd.created_at DESC
        """, (class_id,))

    @staticmethod
    def create(course_id, professor_id, title, description,
               file_url, file_name, file_size_kb=0, promotion_id=None):
        return execute_query("""
            INSERT INTO course_documents
                (course_id, professor_id, title, description,
                 file_url, file_name, file_size_kb, promotion_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (course_id, professor_id, title.strip(),
              description or None, file_url, file_name,
              file_size_kb, promotion_id), fetch="one")

    @staticmethod
    def delete(document_id):
        execute_query("UPDATE course_documents SET is_active=FALSE WHERE id=%s",
                      (document_id,), fetch="none")


# ============================================================
# TRAVAUX PRATIQUES
# ============================================================
class TpAssignmentQueries:

    @staticmethod
    def get_by_class(class_id):
        return execute_query("""
            SELECT t.*, c.name AS course_name, p.name AS professor_name,
                   (SELECT COUNT(*) FROM tp_submissions s
                    WHERE s.tp_assignment_id = t.id) AS submissions_count
            FROM tp_assignments t
            JOIN courses    c ON t.course_id    = c.id
            JOIN professors p ON t.professor_id = p.id
            WHERE t.class_id=%s
            ORDER BY t.created_at DESC
        """, (class_id,))

    @staticmethod
    def get_open_by_class(class_id):
        return execute_query("""
            SELECT t.*, c.name AS course_name, p.name AS professor_name
            FROM tp_assignments t
            JOIN courses    c ON t.course_id    = c.id
            JOIN professors p ON t.professor_id = p.id
            WHERE t.class_id=%s AND t.is_open=TRUE AND t.deadline > NOW()
            ORDER BY t.deadline ASC
        """, (class_id,))

    @staticmethod
    def get_by_professor(professor_id):
        return execute_query("""
            SELECT t.*, c.id AS course_id, c.name AS course_name,
                   c.department_id,
                   d.name AS department_name, d.faculty_id,
                   f.name AS faculty_name,
                   cl.name AS class_name, cl.promotion_id,
                   pr.name AS promotion_name,
                   (SELECT COUNT(*) FROM tp_submissions s
                    WHERE s.tp_assignment_id = t.id) AS submissions_count
            FROM tp_assignments t
            JOIN courses     c  ON t.course_id      = c.id
            JOIN departments d  ON c.department_id  = d.id
            JOIN faculties   f  ON d.faculty_id     = f.id
            JOIN classes     cl ON t.class_id       = cl.id
            JOIN promotions  pr ON cl.promotion_id  = pr.id
            WHERE t.professor_id=%s
            ORDER BY t.created_at DESC
        """, (professor_id,))

    @staticmethod
    def get_by_id(tp_id):
        return execute_query(
            "SELECT * FROM tp_assignments WHERE id=%s",
            (tp_id,), fetch="one"
        )

    @staticmethod
    def create(title, description, course_id, professor_id,
               class_id, deadline, max_file_mb=10,
               subject_url=None, subject_file_name=None):
        return execute_query("""
            INSERT INTO tp_assignments
                (title, description, course_id, professor_id,
                 class_id, deadline, max_file_mb,
                 subject_url, subject_file_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (title.strip(), description or None, course_id,
              professor_id, class_id, deadline, max_file_mb,
              subject_url, subject_file_name), fetch="one")

    @staticmethod
    def toggle_open(tp_id, is_open: bool):
        execute_query("UPDATE tp_assignments SET is_open=%s WHERE id=%s",
                      (is_open, tp_id), fetch="none")

    @staticmethod
    def delete(tp_id):
        execute_query("DELETE FROM tp_assignments WHERE id=%s",
                      (tp_id,), fetch="none")


# ============================================================
# SOUMISSIONS TP
# ============================================================
class TpSubmissionQueries:

    @staticmethod
    def get_by_assignment(tp_assignment_id):
        return execute_query("""
            SELECT sub.*, st.full_name AS student_name,
                   st.student_number
            FROM tp_submissions sub
            JOIN students st ON sub.student_id = st.id
            WHERE sub.tp_assignment_id=%s
            ORDER BY sub.submitted_at DESC
        """, (tp_assignment_id,))

    @staticmethod
    def get_by_student(student_id):
        return execute_query("""
            SELECT sub.*, t.title AS tp_title, t.deadline,
                   c.name AS course_name
            FROM tp_submissions sub
            JOIN tp_assignments t ON sub.tp_assignment_id = t.id
            JOIN courses        c ON t.course_id = c.id
            WHERE sub.student_id=%s
            ORDER BY sub.submitted_at DESC
        """, (student_id,))

    @staticmethod
    def get_by_student_and_tp(student_id, tp_assignment_id):
        return execute_query("""
            SELECT * FROM tp_submissions
            WHERE student_id=%s AND tp_assignment_id=%s
        """, (student_id, tp_assignment_id), fetch="one")

    @staticmethod
    def submit(tp_assignment_id, student_id, file_url,
               file_name, file_size_kb=0):
        return execute_query("""
            INSERT INTO tp_submissions
                (tp_assignment_id, student_id, file_url, file_name, file_size_kb)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tp_assignment_id, student_id)
            DO UPDATE SET file_url=%s, file_name=%s,
                          file_size_kb=%s, submitted_at=NOW()
            RETURNING id
        """, (tp_assignment_id, student_id, file_url, file_name, file_size_kb,
              file_url, file_name, file_size_kb), fetch="one")

    @staticmethod
    def grade(submission_id, grade, comment):
        execute_query("""
            UPDATE tp_submissions
            SET grade=%s, grade_comment=%s, graded_at=NOW()
            WHERE id=%s
        """, (grade, comment or None, submission_id), fetch="none")


# ============================================================
# NOTES
# ============================================================
class GradeQueries:

    @staticmethod
    def get_by_student(student_id):
        """Notes publiées d'un étudiant (tous ses cours, toutes sessions)."""
        return execute_query("""
            SELECT g.*, c.name AS course_name, c.code AS course_code,
                   p.name AS professor_name
            FROM grades g
            JOIN courses    c ON g.course_id    = c.id
            JOIN professors p ON g.professor_id = p.id
            WHERE g.student_id=%s AND g.status = 'publie'
            ORDER BY g.session_name, c.name, g.exam_type
        """, (student_id,))

    @staticmethod
    def get_by_course_and_class(course_id, class_id):
        return execute_query("""
            SELECT g.*, s.full_name AS student_name, s.student_number
            FROM grades g
            JOIN students s ON g.student_id = s.id
            WHERE g.course_id=%s AND s.class_id=%s
            ORDER BY s.full_name
        """, (course_id, class_id))

    @staticmethod
    def get_by_id(grade_id):
        return execute_query(
            "SELECT g.*, c.name AS course_name, s.full_name AS student_name, "
            "s.student_number FROM grades g "
            "JOIN courses c ON g.course_id=c.id "
            "JOIN students s ON g.student_id=s.id "
            "WHERE g.id=%s",
            (grade_id,), fetch="one"
        )

    @staticmethod
    def can_prof_modify(grade_id) -> bool:
        """Retourne True si la note a été saisie il y a moins de 48h."""
        row = execute_query(
            "SELECT created_at FROM grades WHERE id=%s",
            (grade_id,), fetch="one"
        )
        if not row or not row.get("created_at"):
            return True
        from datetime import datetime, timezone
        created = row["created_at"]
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() < 48 * 3600

    @staticmethod
    def submit_session(professor_id, class_id, session_name):
        """Passe toutes les notes 'brouillon' du prof pour cette classe/session en 'soumis'."""
        result = execute_query("""
            UPDATE grades SET status='soumis', updated_at=NOW()
            WHERE professor_id=%s
              AND student_id IN (SELECT id FROM students WHERE class_id=%s)
              AND session_name=%s
              AND status='brouillon'
            RETURNING id
        """, (professor_id, class_id, session_name))
        return len(result) if result else 0

    @staticmethod
    def validate_session(class_id, session_name):
        """Département valide toutes les notes soumises/brouillon pour cette classe/session."""
        execute_query("""
            UPDATE grades SET status='valide', updated_at=NOW()
            WHERE student_id IN (SELECT id FROM students WHERE class_id=%s)
              AND session_name=%s
              AND status IN ('brouillon', 'soumis')
        """, (class_id, session_name), fetch="none")

    @staticmethod
    def get_status_summary(class_id, session_name):
        """Compte les notes par statut pour une classe/session."""
        return execute_query("""
            SELECT status, COUNT(*) AS cnt
            FROM grades
            WHERE student_id IN (SELECT id FROM students WHERE class_id=%s)
              AND session_name=%s
            GROUP BY status
            ORDER BY status
        """, (class_id, session_name))

    @staticmethod
    def upsert(student_id, course_id, professor_id,
               grade, max_grade, exam_type, comment=None,
               session_name='Principale', motif=None):
        existing = execute_query("""
            SELECT id, grade, max_grade, comment, status
            FROM grades
            WHERE student_id=%s AND course_id=%s
              AND exam_type=%s AND session_name=%s
        """, (student_id, course_id, exam_type, session_name), fetch="one")

        if existing:
            old_grade   = existing["grade"]
            old_max     = existing["max_grade"]
            old_comment = existing["comment"]
            # Si publiée, ne pas toucher au statut ; sinon repasser en brouillon
            execute_query("""
                UPDATE grades
                SET grade=%s, max_grade=%s, professor_id=%s,
                    comment=%s, updated_at=NOW(),
                    status = CASE WHEN status = 'publie' THEN 'publie' ELSE 'brouillon' END
                WHERE id=%s
            """, (grade, max_grade, professor_id, comment, existing["id"]), fetch="none")
            execute_query("""
                INSERT INTO grade_audit
                    (student_id, course_id, exam_type, session_name,
                     old_grade, new_grade, max_grade, old_max_grade,
                     old_comment, new_comment,
                     changed_by_professor_id, motif, action)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'update')
            """, (student_id, course_id, exam_type, session_name,
                  old_grade, grade, max_grade, old_max,
                  old_comment, comment,
                  professor_id, motif), fetch="none")
        else:
            execute_query("""
                INSERT INTO grades
                    (student_id, course_id, professor_id,
                     grade, max_grade, exam_type, comment, session_name,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (student_id, course_id, professor_id,
                  grade, max_grade, exam_type, comment, session_name), fetch="none")
            new_row = execute_query("""
                SELECT id FROM grades
                WHERE student_id=%s AND course_id=%s
                  AND exam_type=%s AND session_name=%s
            """, (student_id, course_id, exam_type, session_name), fetch="one")
            execute_query("""
                INSERT INTO grade_audit
                    (student_id, course_id, exam_type, session_name,
                     new_grade, max_grade, new_comment,
                     changed_by_professor_id, motif, action)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'create')
            """, (student_id, course_id, exam_type, session_name,
                  grade, max_grade, comment,
                  professor_id, motif), fetch="none")

    @staticmethod
    def update_direct(grade_id, new_grade, new_max, new_comment,
                      motif, professor_id):
        """Modification directe (< 48h). Enregistre l'audit."""
        old = execute_query(
            "SELECT grade, max_grade, comment, student_id, course_id, "
            "exam_type, session_name FROM grades WHERE id=%s",
            (grade_id,), fetch="one"
        )
        if not old:
            raise ValueError("Note introuvable.")
        execute_query("""
            UPDATE grades SET grade=%s, max_grade=%s, comment=%s, updated_at=NOW()
            WHERE id=%s
        """, (new_grade, new_max, new_comment, grade_id), fetch="none")
        execute_query("""
            INSERT INTO grade_audit
                (student_id, course_id, exam_type, session_name,
                 old_grade, new_grade, max_grade, old_max_grade,
                 old_comment, new_comment,
                 changed_by_professor_id, motif, action)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'update')
        """, (old["student_id"], old["course_id"], old["exam_type"], old["session_name"],
              old["grade"], new_grade, new_max, old["max_grade"],
              old["comment"], new_comment,
              professor_id, motif), fetch="none")

    @staticmethod
    def get_sessions_by_class(class_id):
        """Sessions distinctes ayant des notes pour une classe."""
        return execute_query("""
            SELECT DISTINCT g.session_name
            FROM grades g
            JOIN students s ON g.student_id = s.id
            WHERE s.class_id = %s
            ORDER BY g.session_name
        """, (class_id,))

    @staticmethod
    def get_by_class_session(class_id, session_name):
        """Toutes les notes d'une classe pour une session donnée."""
        return execute_query("""
            SELECT g.*, s.full_name AS student_name, s.student_number,
                   s.email AS student_email,
                   c.name AS course_name, c.code AS course_code,
                   COALESCE(c.weight, 1.0)    AS course_weight,
                   COALESCE(c.credits_ec, 1.0) AS credits_ec,
                   c.ue_id,
                   ue.name        AS ue_name,
                   ue.code        AS ue_code,
                   ue.credits     AS ue_credits,
                   ue.group_label AS ue_group
            FROM grades g
            JOIN students s ON g.student_id = s.id
            JOIN courses  c ON g.course_id  = c.id
            LEFT JOIN unites_enseignement ue ON c.ue_id = ue.id
            WHERE s.class_id = %s AND g.session_name = %s
            ORDER BY s.full_name, ue.group_label NULLS LAST,
                     ue.code NULLS LAST, c.name, g.exam_type
        """, (class_id, session_name))

    @staticmethod
    def publish_session(class_id, session_name):
        """Publie toutes les notes d'une session pour une classe (statut → publie)."""
        execute_query("""
            UPDATE grades SET is_published = TRUE, status = 'publie', updated_at = NOW()
            WHERE student_id IN (SELECT id FROM students WHERE class_id = %s)
              AND session_name = %s
        """, (class_id, session_name), fetch="none")

    @staticmethod
    def get_published_sessions_by_student(student_id):
        """Sessions publiées ayant des notes pour un étudiant."""
        return execute_query("""
            SELECT DISTINCT session_name FROM grades
            WHERE student_id = %s AND status = 'publie'
            ORDER BY session_name
        """, (student_id,))

    @staticmethod
    def get_bulletin_by_student(student_id, session_name):
        """Notes publiées d'un étudiant pour une session (inclut infos UE/EC)."""
        return execute_query("""
            SELECT g.*,
                   c.name  AS course_name,  c.code AS course_code,
                   COALESCE(c.weight, 1.0)    AS course_weight,
                   COALESCE(c.credits_ec, 1.0) AS credits_ec,
                   c.ue_id,
                   ue.name        AS ue_name,
                   ue.code        AS ue_code,
                   ue.credits     AS ue_credits,
                   ue.group_label AS ue_group,
                   p.name AS professor_name
            FROM grades g
            JOIN courses    c  ON g.course_id    = c.id
            JOIN professors p  ON g.professor_id = p.id
            LEFT JOIN unites_enseignement ue ON c.ue_id = ue.id
            WHERE g.student_id = %s AND g.session_name = %s
              AND g.status = 'publie'
            ORDER BY ue.group_label NULLS LAST, ue.code NULLS LAST,
                     c.name, g.exam_type
        """, (student_id, session_name))

    @staticmethod
    def get_class_rank(student_id, class_id, session_name):
        """Rang de l'étudiant (1 = premier) dans sa classe pour une session publiée."""
        row = execute_query("""
            WITH avgs AS (
                SELECT g.student_id,
                       SUM(g.grade / NULLIF(g.max_grade, 0) * 20
                           * COALESCE(c.weight, 1.0))
                       / NULLIF(SUM(COALESCE(c.weight, 1.0)), 0) AS avg20
                FROM grades g
                JOIN students s ON g.student_id = s.id
                JOIN courses  c ON g.course_id  = c.id
                WHERE s.class_id = %s
                  AND g.session_name = %s
                  AND g.is_published = TRUE
                GROUP BY g.student_id
            )
            SELECT COUNT(*) + 1 AS rank
            FROM avgs
            WHERE avg20 > (SELECT avg20 FROM avgs WHERE student_id = %s)
        """, (class_id, session_name, student_id), fetch="one")
        return row["rank"] if row else None

    @staticmethod
    def get_all_sessions_for_annual(class_id):
        """Toutes les notes publiées des 4 sessions standard pour la délibération annuelle."""
        return execute_query("""
            SELECT g.student_id, g.course_id, g.session_name,
                   g.grade, g.max_grade, g.exam_type,
                   s.full_name AS student_name, s.student_number,
                   c.name AS course_name,
                   COALESCE(c.credits_ec, 1.0) AS credits_ec,
                   c.ue_id,
                   ue.name        AS ue_name,
                   ue.code        AS ue_code,
                   ue.credits     AS ue_credits,
                   ue.group_label AS ue_group
            FROM grades g
            JOIN students s ON g.student_id = s.id
            JOIN courses  c ON g.course_id  = c.id
            LEFT JOIN unites_enseignement ue ON c.ue_id = ue.id
            WHERE s.class_id = %s
              AND g.status = 'publie'
              AND g.session_name IN (
                  'S1 - Session Normale', 'S1 - Session de Rattrapage',
                  'S2 - Session Normale', 'S2 - Session de Rattrapage'
              )
            ORDER BY s.full_name, g.session_name, c.name
        """, (class_id,))

    @staticmethod
    def get_nval_course_ids_by_student(student_id, session_name):
        """Cours où l'étudiant a une note < 10/20 dans une session publiée."""
        rows = execute_query("""
            SELECT DISTINCT g.course_id
            FROM grades g
            WHERE g.student_id = %s AND g.session_name = %s
              AND g.status = 'publie'
              AND (g.grade::float / NULLIF(g.max_grade, 0) * 20) < 10.0
        """, (student_id, session_name))
        return {r["course_id"] for r in (rows or [])}


# ============================================================
# ANALYTIQUES
# ============================================================
class AnalyticsQueries:

    @staticmethod
    def get_global_summary():
        return execute_query("""
            SELECT
                (SELECT COUNT(*) FROM universities   WHERE is_active=TRUE)  AS uni_count,
                (SELECT COUNT(*) FROM students       WHERE is_active=TRUE)  AS student_count,
                (SELECT COUNT(*) FROM professors     WHERE is_active=TRUE)  AS prof_count,
                (SELECT COUNT(*) FROM tp_assignments)                        AS tp_count,
                (SELECT COUNT(*) FROM tp_submissions)                        AS submission_count,
                (SELECT COUNT(*) FROM grades)                                AS grade_count
        """, fetch="one")

    @staticmethod
    def get_universities_summary():
        return execute_query("""
            SELECT u.id, u.name, u.primary_color,
                (SELECT COUNT(*) FROM students st
                 WHERE st.university_id=u.id AND st.is_active=TRUE)          AS students,
                (SELECT COUNT(*) FROM professors p
                 WHERE p.university_id=u.id AND p.is_active=TRUE)            AS professors,
                (SELECT COUNT(*) FROM schedules s
                 JOIN classes    cl ON s.class_id=cl.id
                 JOIN promotions pr ON cl.promotion_id=pr.id
                 JOIN departments d ON pr.department_id=d.id
                 JOIN faculties   f ON d.faculty_id=f.id
                 WHERE f.university_id=u.id AND s.is_active=TRUE)            AS schedules
            FROM universities u
            WHERE u.is_active=TRUE
            ORDER BY students DESC
        """)

    @staticmethod
    def get_recent_student_registrations(days=30):
        return execute_query("""
            SELECT DATE(created_at) AS date, COUNT(*) AS count
            FROM students
            WHERE created_at >= NOW() - (%s || ' days')::INTERVAL
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (days,))

    @staticmethod
    def get_course_performance(class_id, session_name):
        """Moyenne, min, max, écart-type par cours pour une classe/session."""
        return execute_query("""
            SELECT
                c.id                                                    AS course_id,
                c.name                                                  AS course_name,
                COALESCE(c.weight, 1)                                   AS weight,
                p.name                                                  AS professor_name,
                COUNT(DISTINCT g.student_id)                           AS nb_students,
                ROUND(AVG(g.grade / NULLIF(g.max_grade,0) * 20)::NUMERIC, 2)    AS avg_20,
                ROUND(MIN(g.grade / NULLIF(g.max_grade,0) * 20)::NUMERIC, 2)    AS min_20,
                ROUND(MAX(g.grade / NULLIF(g.max_grade,0) * 20)::NUMERIC, 2)    AS max_20,
                ROUND(STDDEV(g.grade / NULLIF(g.max_grade,0) * 20)::NUMERIC, 2) AS std_dev
            FROM grades g
            JOIN courses    c ON g.course_id    = c.id
            JOIN professors p ON g.professor_id = p.id
            WHERE g.student_id IN (SELECT id FROM students WHERE class_id = %s)
              AND g.session_name = %s
            GROUP BY c.id, c.name, c.weight, p.name
            ORDER BY avg_20 DESC NULLS LAST
        """, (class_id, session_name))

    @staticmethod
    def get_at_risk_students(class_id, session_name):
        """Étudiants avec une décision Session 2 ou Ajourné (depuis student_session_results)."""
        return execute_query("""
            SELECT ssr.student_id, ssr.average, ssr.rank, ssr.decision,
                   s.full_name AS student_name, s.student_number, s.email
            FROM student_session_results ssr
            JOIN students s ON ssr.student_id = s.id
            WHERE ssr.class_id = %s AND ssr.session_name = %s
              AND ssr.decision IN ('Session 2', 'Ajourné')
            ORDER BY ssr.average ASC
        """, (class_id, session_name))

    @staticmethod
    def get_top_students(class_id, session_name, limit=5):
        """Meilleurs étudiants admis (depuis student_session_results)."""
        return execute_query("""
            SELECT ssr.student_id, ssr.average, ssr.rank, ssr.decision,
                   s.full_name AS student_name, s.student_number
            FROM student_session_results ssr
            JOIN students s ON ssr.student_id = s.id
            WHERE ssr.class_id = %s AND ssr.session_name = %s
              AND ssr.decision = 'Admis'
            ORDER BY ssr.average DESC
            LIMIT %s
        """, (class_id, session_name, limit))

    @staticmethod
    def get_session_decision_summary(class_id, session_name):
        """Compte Admis / Session 2 / Ajourné pour une classe/session."""
        return execute_query("""
            SELECT decision, COUNT(*) AS cnt,
                   ROUND(AVG(average)::NUMERIC, 2) AS avg_decision
            FROM student_session_results
            WHERE class_id = %s AND session_name = %s
            GROUP BY decision
            ORDER BY decision
        """, (class_id, session_name))


# ============================================================
# FILIÈRES
# ============================================================
class FiliereQueries:

    @staticmethod
    def get_by_department(department_id):
        return execute_query(
            "SELECT * FROM filieres WHERE department_id=%s AND is_active=TRUE ORDER BY name",
            (department_id,)
        )

    @staticmethod
    def get_by_id(filiere_id):
        return execute_query(
            "SELECT f.*, d.name AS department_name FROM filieres f "
            "JOIN departments d ON f.department_id=d.id WHERE f.id=%s",
            (filiere_id,), fetch="one"
        )

    @staticmethod
    def create(name, department_id, code="", description=""):
        return execute_query(
            "INSERT INTO filieres (name,code,department_id,description) "
            "VALUES (%s,%s,%s,%s) RETURNING id",
            (name, code or None, department_id, description or ""), fetch="one"
        )

    @staticmethod
    def update(filiere_id, name, code="", description=""):
        execute_query(
            "UPDATE filieres SET name=%s,code=%s,description=%s WHERE id=%s",
            (name, code or None, description or "", filiere_id), fetch="none"
        )

    @staticmethod
    def delete(filiere_id):
        execute_query("UPDATE filieres SET is_active=FALSE WHERE id=%s",
                      (filiere_id,), fetch="none")


# ============================================================
# OPTIONS D'ÉTUDE
# ============================================================
class OptionEtudeQueries:

    @staticmethod
    def get_by_filiere(filiere_id):
        return execute_query(
            "SELECT * FROM options_etude WHERE filiere_id=%s AND is_active=TRUE ORDER BY name",
            (filiere_id,)
        )

    @staticmethod
    def get_by_department(department_id):
        return execute_query("""
            SELECT o.*, f.name AS filiere_name
            FROM options_etude o
            JOIN filieres f ON o.filiere_id=f.id
            WHERE f.department_id=%s AND o.is_active=TRUE AND f.is_active=TRUE
            ORDER BY f.name, o.name
        """, (department_id,))

    @staticmethod
    def get_by_id(option_id):
        return execute_query(
            "SELECT o.*, f.name AS filiere_name FROM options_etude o "
            "JOIN filieres f ON o.filiere_id=f.id WHERE o.id=%s",
            (option_id,), fetch="one"
        )

    @staticmethod
    def create(name, filiere_id, code="", description=""):
        return execute_query(
            "INSERT INTO options_etude (name,code,filiere_id,description) "
            "VALUES (%s,%s,%s,%s) RETURNING id",
            (name, code or None, filiere_id, description or ""), fetch="one"
        )

    @staticmethod
    def update(option_id, name, code="", description=""):
        execute_query(
            "UPDATE options_etude SET name=%s,code=%s,description=%s WHERE id=%s",
            (name, code or None, description or "", option_id), fetch="none"
        )

    @staticmethod
    def delete(option_id):
        execute_query("UPDATE options_etude SET is_active=FALSE WHERE id=%s",
                      (option_id,), fetch="none")


# ============================================================
# INSCRIPTIONS ACADÉMIQUES
# ============================================================
class AcademicEnrollmentQueries:

    STATUSES = ["inscrit", "admis", "redoublant", "transfere", "abandonne"]
    STATUS_LABELS = {
        "inscrit":    "Inscrit",
        "admis":      "Admis(e)",
        "redoublant": "Redoublant(e)",
        "transfere":  "Transféré(e)",
        "abandonne":  "Abandonné(e)",
    }

    @staticmethod
    def enroll(student_id, class_id, promotion_id, academic_year,
               option_id=None, status="inscrit", notes=None, changed_by=None):
        return execute_query("""
            INSERT INTO academic_enrollments
                (student_id, class_id, promotion_id, option_id,
                 academic_year, status, notes, changed_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (student_id, academic_year) DO UPDATE
                SET class_id=EXCLUDED.class_id,
                    promotion_id=EXCLUDED.promotion_id,
                    option_id=EXCLUDED.option_id,
                    status=EXCLUDED.status,
                    notes=EXCLUDED.notes,
                    changed_by=EXCLUDED.changed_by,
                    updated_at=NOW()
            RETURNING id
        """, (student_id, class_id, promotion_id, option_id,
              academic_year, status, notes, changed_by), fetch="one")

    @staticmethod
    def get_by_student(student_id):
        return execute_query("""
            SELECT ae.*, cl.name AS class_name, pr.name AS promotion_name,
                   o.name AS option_name, ae.academic_year, ae.status
            FROM academic_enrollments ae
            JOIN classes    cl ON ae.class_id     = cl.id
            JOIN promotions pr ON ae.promotion_id = pr.id
            LEFT JOIN options_etude o ON ae.option_id = o.id
            WHERE ae.student_id = %s
            ORDER BY ae.academic_year DESC
        """, (student_id,))

    @staticmethod
    def get_by_class_year(class_id, academic_year):
        return execute_query("""
            SELECT ae.*, s.full_name AS student_name, s.student_number,
                   o.name AS option_name
            FROM academic_enrollments ae
            JOIN students       s ON ae.student_id = s.id
            LEFT JOIN options_etude o ON ae.option_id = o.id
            WHERE ae.class_id = %s AND ae.academic_year = %s
            ORDER BY s.full_name
        """, (class_id, academic_year))

    @staticmethod
    def update_status(enrollment_id, status, notes=None, changed_by=None):
        execute_query("""
            UPDATE academic_enrollments
            SET status=%s, notes=%s, changed_by=%s, updated_at=NOW()
            WHERE id=%s
        """, (status, notes, changed_by, enrollment_id), fetch="none")

    @staticmethod
    def get_current(student_id, academic_year):
        return execute_query("""
            SELECT ae.*, cl.name AS class_name, pr.name AS promotion_name,
                   o.name AS option_name
            FROM academic_enrollments ae
            JOIN classes    cl ON ae.class_id     = cl.id
            JOIN promotions pr ON ae.promotion_id = pr.id
            LEFT JOIN options_etude o ON ae.option_id = o.id
            WHERE ae.student_id=%s AND ae.academic_year=%s
        """, (student_id, academic_year), fetch="one")


# ============================================================
# PRÉSENCES
# ============================================================
class AttendanceQueries:

    @staticmethod
    def record(schedule_id, student_id, status="present", recorded_by=None, note=None):
        execute_query("""
            INSERT INTO attendances (schedule_id, student_id, status, recorded_by, note)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (schedule_id, student_id) DO UPDATE
                SET status=EXCLUDED.status,
                    recorded_by=EXCLUDED.recorded_by,
                    note=EXCLUDED.note,
                    recorded_at=NOW()
        """, (schedule_id, student_id, status, recorded_by, note), fetch="none")

    @staticmethod
    def get_by_schedule(schedule_id):
        return execute_query("""
            SELECT a.*, s.full_name AS student_name, s.student_number
            FROM attendances a
            JOIN students s ON a.student_id = s.id
            WHERE a.schedule_id = %s
            ORDER BY s.full_name
        """, (schedule_id,))

    @staticmethod
    def get_student_stats(student_id, class_id=None):
        """Retourne le taux de présence par cours pour un étudiant."""
        extra = "AND sch.class_id = %s" if class_id else ""
        params = (student_id, class_id) if class_id else (student_id,)
        return execute_query(f"""
            SELECT
                COALESCE(c.name, sch.slot_label, 'Jour Férié') AS course_name,
                COUNT(*) AS total_seances,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS presences,
                SUM(CASE WHEN a.status = 'absent'  THEN 1 ELSE 0 END) AS absences,
                SUM(CASE WHEN a.status = 'justifie' THEN 1 ELSE 0 END) AS justifies,
                ROUND(
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)::numeric
                    / NULLIF(COUNT(*), 0) * 100, 1
                ) AS taux_presence
            FROM attendances a
            JOIN schedules sch ON a.schedule_id = sch.id
            LEFT JOIN courses c ON sch.course_id = c.id
            WHERE a.student_id = %s {extra}
            GROUP BY COALESCE(c.name, sch.slot_label, 'Jour Férié')
            ORDER BY course_name
        """, params)

    @staticmethod
    def get_stats_by_class(class_id):
        """Retourne, pour chaque étudiant d'une classe, ses stats de présence par cours."""
        return execute_query("""
            SELECT
                s.id AS student_id,
                s.full_name AS student_name,
                s.student_number,
                COALESCE(c.name, sch.slot_label, 'Autre') AS course_name,
                COUNT(*) AS total_seances,
                SUM(CASE WHEN a.status = 'present'  THEN 1 ELSE 0 END) AS presences,
                SUM(CASE WHEN a.status = 'absent'   THEN 1 ELSE 0 END) AS absences,
                SUM(CASE WHEN a.status = 'justifie' THEN 1 ELSE 0 END) AS justifies,
                ROUND(
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)::numeric
                    / NULLIF(COUNT(*), 0) * 100, 1
                ) AS taux_presence
            FROM attendances a
            JOIN schedules sch ON a.schedule_id = sch.id
            JOIN students  s   ON a.student_id  = s.id
            LEFT JOIN courses c ON sch.course_id = c.id
            WHERE sch.class_id = %s
            GROUP BY s.id, s.full_name, s.student_number,
                     COALESCE(c.name, sch.slot_label, 'Autre')
            ORDER BY s.full_name, course_name
        """, (class_id,))

    @staticmethod
    def get_absences_by_class(class_id):
        """Retourne le nombre total d'absences non justifiées par étudiant dans une classe."""
        return execute_query("""
            SELECT
                s.id AS student_id,
                s.full_name AS student_name,
                s.student_number,
                COUNT(*) FILTER (WHERE a.status = 'absent')   AS absences,
                COUNT(*) FILTER (WHERE a.status = 'justifie') AS justifies,
                COUNT(*) FILTER (WHERE a.status = 'present')  AS presences,
                COUNT(*) AS total_seances
            FROM attendances a
            JOIN schedules sch ON a.schedule_id = sch.id
            JOIN students  s   ON a.student_id  = s.id
            WHERE sch.class_id = %s
            GROUP BY s.id, s.full_name, s.student_number
            ORDER BY absences DESC, s.full_name
        """, (class_id,))


# ============================================================
# MESSAGES PROF → CLASSE
# ============================================================
class ClassMessageQueries:

    @staticmethod
    def create(professor_id, class_id, subject, body, is_urgent=False):
        return execute_query("""
            INSERT INTO class_messages (professor_id, class_id, subject, body, is_urgent)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (professor_id, class_id, subject, body, is_urgent), fetch="one")

    @staticmethod
    def get_by_class(class_id, limit=50):
        return execute_query("""
            SELECT m.*, p.name AS professor_name
            FROM class_messages m
            JOIN professors p ON m.professor_id = p.id
            WHERE m.class_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s
        """, (class_id, limit))

    @staticmethod
    def get_by_professor(professor_id, limit=50):
        return execute_query("""
            SELECT m.*, cl.name AS class_name
            FROM class_messages m
            JOIN classes cl ON m.class_id = cl.id
            WHERE m.professor_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s
        """, (professor_id, limit))

    @staticmethod
    def delete(message_id):
        execute_query("DELETE FROM class_messages WHERE id=%s",
                      (message_id,), fetch="none")


# ============================================================
# RÉCLAMATIONS DE NOTES
# ============================================================
class GradeClaimQueries:

    @staticmethod
    def create(grade_id, student_id, reason):
        return execute_query("""
            INSERT INTO grade_claims (grade_id, student_id, reason)
            VALUES (%s,%s,%s) RETURNING id
        """, (grade_id, student_id, reason), fetch="one")

    @staticmethod
    def get_by_student(student_id):
        return execute_query("""
            SELECT gc.*, g.grade, g.max_grade, g.exam_type, g.session_name,
                   c.name AS course_name
            FROM grade_claims gc
            JOIN grades  g ON gc.grade_id  = g.id
            JOIN courses c ON g.course_id  = c.id
            WHERE gc.student_id = %s
            ORDER BY gc.created_at DESC
        """, (student_id,))

    @staticmethod
    def get_pending_by_professor(professor_id):
        return execute_query("""
            SELECT gc.*, g.grade, g.max_grade, g.exam_type, g.session_name,
                   c.id AS course_id, c.name AS course_name, c.department_id,
                   d.name AS department_name, d.faculty_id,
                   f.name AS faculty_name,
                   s.full_name AS student_name, s.student_number
            FROM grade_claims gc
            JOIN grades      g ON gc.grade_id    = g.id
            JOIN courses     c ON g.course_id    = c.id
            JOIN departments d ON c.department_id = d.id
            JOIN faculties   f ON d.faculty_id   = f.id
            JOIN students    s ON gc.student_id  = s.id
            WHERE g.professor_id = %s AND gc.status = 'pending'
            ORDER BY gc.created_at DESC
        """, (professor_id,))

    @staticmethod
    def get_pending_by_department(department_id):
        return execute_query("""
            SELECT gc.*, g.grade, g.max_grade, g.exam_type, g.session_name,
                   c.name AS course_name,
                   s.full_name AS student_name, s.student_number,
                   cl.name AS class_name,
                   p.name AS professor_name
            FROM grade_claims gc
            JOIN grades    g  ON gc.grade_id   = g.id
            JOIN courses   c  ON g.course_id   = c.id
            JOIN students  s  ON gc.student_id = s.id
            JOIN classes   cl ON s.class_id    = cl.id
            JOIN professors p  ON g.professor_id = p.id
            JOIN professor_faculty_affiliations pfa ON pfa.professor_id = p.id
            JOIN departments d ON d.faculty_id = pfa.faculty_id
            WHERE d.id = %s AND gc.status = 'pending'
            ORDER BY gc.created_at DESC
        """, (department_id,))

    @staticmethod
    def review(claim_id, status, response, reviewed_by):
        execute_query("""
            UPDATE grade_claims
            SET status=%s, response=%s, reviewed_by=%s, updated_at=NOW()
            WHERE id=%s
        """, (status, response, reviewed_by, claim_id), fetch="none")


# ============================================================
# AUDIT DES NOTES
# ============================================================
class GradeAuditQueries:

    @staticmethod
    def get_by_grade(grade_id):
        """Historique complet d'une note (par grade_id)."""
        row = execute_query(
            "SELECT student_id, course_id, exam_type, session_name FROM grades WHERE id=%s",
            (grade_id,), fetch="one"
        )
        if not row:
            return []
        return execute_query("""
            SELECT ga.*, p.name AS professor_name,
                   u.name AS reviewed_by_name
            FROM grade_audit ga
            LEFT JOIN professors p ON ga.changed_by_professor_id = p.id
            LEFT JOIN users      u ON ga.reviewed_by_id = u.id
            WHERE ga.student_id=%s AND ga.course_id=%s
              AND ga.exam_type=%s AND ga.session_name=%s
            ORDER BY ga.changed_at DESC
        """, (row["student_id"], row["course_id"],
              row["exam_type"], row["session_name"]))

    @staticmethod
    def get_by_student_session(student_id, session_name):
        return execute_query("""
            SELECT ga.*, c.name AS course_name, p.name AS professor_name
            FROM grade_audit ga
            JOIN courses     c ON ga.course_id             = c.id
            LEFT JOIN professors p ON ga.changed_by_professor_id = p.id
            WHERE ga.student_id=%s AND ga.session_name=%s
            ORDER BY ga.changed_at DESC
        """, (student_id, session_name))


# ============================================================
# DEMANDES DE MODIFICATION DE NOTES (après 48h)
# ============================================================
class GradeModificationRequestQueries:

    @staticmethod
    def create(grade_id, professor_id, requested_grade, requested_max,
               requested_comment, motif, current_grade, current_max, current_comment):
        return execute_query("""
            INSERT INTO grade_modification_requests
                (grade_id, professor_id,
                 current_grade, current_max, current_comment,
                 requested_grade, requested_max, requested_comment,
                 motif)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (grade_id, professor_id,
              current_grade, current_max, current_comment,
              requested_grade, requested_max, requested_comment,
              motif), fetch="one")

    @staticmethod
    def get_pending_by_department(department_id):
        return execute_query("""
            SELECT r.*,
                   g.exam_type, g.session_name,
                   c.name AS course_name,
                   s.full_name AS student_name, s.student_number,
                   p.name AS professor_name,
                   cl.name AS class_name
            FROM grade_modification_requests r
            JOIN grades   g  ON r.grade_id     = g.id
            JOIN courses  c  ON g.course_id    = c.id
            JOIN students s  ON g.student_id   = s.id
            JOIN classes  cl ON s.class_id     = cl.id
            JOIN professors p ON r.professor_id = p.id
            JOIN professor_faculty_affiliations pfa ON pfa.professor_id = p.id
            JOIN departments d ON d.faculty_id = pfa.faculty_id
            WHERE r.status = 'pending'
              AND d.id = %s
            ORDER BY r.requested_at DESC
        """, (department_id,))

    @staticmethod
    def get_by_professor(professor_id):
        return execute_query("""
            SELECT r.*,
                   g.exam_type, g.session_name,
                   c.name AS course_name,
                   s.full_name AS student_name
            FROM grade_modification_requests r
            JOIN grades   g  ON r.grade_id   = g.id
            JOIN courses  c  ON g.course_id  = c.id
            JOIN students s  ON g.student_id = s.id
            WHERE r.professor_id = %s
            ORDER BY r.requested_at DESC
            LIMIT 50
        """, (professor_id,))

    @staticmethod
    def approve(request_id, admin_user_id, admin_response):
        """Valide la demande et applique la modification sur la note."""
        req = execute_query(
            "SELECT * FROM grade_modification_requests WHERE id=%s",
            (request_id,), fetch="one"
        )
        if not req:
            raise ValueError("Demande introuvable.")

        old = execute_query(
            "SELECT student_id, course_id, exam_type, session_name, "
            "grade, max_grade, comment FROM grades WHERE id=%s",
            (req["grade_id"],), fetch="one"
        )
        if not old:
            raise ValueError("Note introuvable.")

        execute_query("""
            UPDATE grades
            SET grade=%s, max_grade=%s, comment=%s, updated_at=NOW()
            WHERE id=%s
        """, (req["requested_grade"], req["requested_max"],
              req["requested_comment"], req["grade_id"]), fetch="none")

        execute_query("""
            INSERT INTO grade_audit
                (student_id, course_id, exam_type, session_name,
                 old_grade, new_grade, max_grade, old_max_grade,
                 old_comment, new_comment,
                 changed_by_professor_id, motif, action, reviewed_by_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'request_approved',%s)
        """, (old["student_id"], old["course_id"], old["exam_type"], old["session_name"],
              old["grade"], req["requested_grade"], req["requested_max"], old["max_grade"],
              old["comment"], req["requested_comment"],
              req["professor_id"], req["motif"], admin_user_id), fetch="none")

        execute_query("""
            UPDATE grade_modification_requests
            SET status='approved', admin_response=%s,
                reviewed_by=%s, reviewed_at=NOW()
            WHERE id=%s
        """, (admin_response, admin_user_id, request_id), fetch="none")

    @staticmethod
    def reject(request_id, admin_user_id, admin_response):
        old_g = execute_query(
            "SELECT r.*, g.student_id, g.course_id, g.exam_type, g.session_name "
            "FROM grade_modification_requests r JOIN grades g ON r.grade_id=g.id "
            "WHERE r.id=%s", (request_id,), fetch="one"
        )
        execute_query("""
            INSERT INTO grade_audit
                (student_id, course_id, exam_type, session_name,
                 old_grade, new_grade, max_grade,
                 changed_by_professor_id, motif, action, reviewed_by_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'request_rejected',%s)
        """, (old_g["student_id"], old_g["course_id"],
              old_g["exam_type"], old_g["session_name"],
              old_g["current_grade"], old_g["current_grade"],
              old_g["current_max"],
              old_g["professor_id"], old_g["motif"], admin_user_id), fetch="none")

        execute_query("""
            UPDATE grade_modification_requests
            SET status='rejected', admin_response=%s,
                reviewed_by=%s, reviewed_at=NOW()
            WHERE id=%s
        """, (admin_response, admin_user_id, request_id), fetch="none")


# ============================================================
# BULLETINS
# ============================================================
class BulletinQueries:

    STATUSES = ["brouillon", "valide", "publie"]
    STATUS_LABELS = {
        "brouillon": "Brouillon",
        "valide":    "Validé",
        "publie":    "Publié",
    }

    @staticmethod
    def upsert(class_id, session_name, academic_year,
               created_by=None, notes=None):
        """Crée ou met à jour un bulletin (brouillon par défaut)."""
        return execute_query("""
            INSERT INTO bulletins (class_id, session_name, academic_year,
                                   status, notes, created_by)
            VALUES (%s, %s, %s, 'brouillon', %s, %s)
            ON CONFLICT (class_id, session_name, academic_year) DO UPDATE
                SET notes      = EXCLUDED.notes,
                    updated_at = NOW()
            RETURNING id
        """, (class_id, session_name, academic_year, notes, created_by),
                             fetch="one")

    @staticmethod
    def validate(class_id, session_name, academic_year, validated_by=None):
        execute_query("""
            UPDATE bulletins
            SET status='valide', validated_by=%s, validated_at=NOW(), updated_at=NOW()
            WHERE class_id=%s AND session_name=%s AND academic_year=%s
        """, (validated_by, class_id, session_name, academic_year), fetch="none")

    @staticmethod
    def publish(class_id, session_name, academic_year, published_by=None):
        execute_query("""
            UPDATE bulletins
            SET status='publie', published_by=%s, published_at=NOW(), updated_at=NOW()
            WHERE class_id=%s AND session_name=%s AND academic_year=%s
        """, (published_by, class_id, session_name, academic_year), fetch="none")

    @staticmethod
    def get(class_id, session_name, academic_year):
        return execute_query("""
            SELECT b.*,
                   u_c.name AS created_by_name,
                   u_v.name AS validated_by_name,
                   u_p.name AS published_by_name
            FROM bulletins b
            LEFT JOIN users u_c ON b.created_by   = u_c.id
            LEFT JOIN users u_v ON b.validated_by  = u_v.id
            LEFT JOIN users u_p ON b.published_by  = u_p.id
            WHERE b.class_id=%s AND b.session_name=%s AND b.academic_year=%s
        """, (class_id, session_name, academic_year), fetch="one")

    @staticmethod
    def get_by_class(class_id):
        return execute_query("""
            SELECT b.*,
                   u_p.name AS published_by_name
            FROM bulletins b
            LEFT JOIN users u_p ON b.published_by = u_p.id
            WHERE b.class_id=%s
            ORDER BY b.academic_year DESC, b.session_name
        """, (class_id,))

    @staticmethod
    def get_by_department(department_id):
        return execute_query("""
            SELECT b.*, cl.name AS class_name, pr.name AS promotion_name
            FROM bulletins b
            JOIN classes    cl ON b.class_id      = cl.id
            JOIN promotions pr ON cl.promotion_id = pr.id
            WHERE pr.department_id = %s
            ORDER BY b.academic_year DESC, cl.name, b.session_name
        """, (department_id,))


# ============================================================
# RÉSULTATS DE SESSION (décisions calculées)
# ============================================================
class StudentResultsQueries:

    @staticmethod
    def upsert(student_id, class_id, session_name, academic_year,
               average, rank, decision,
               threshold_admis=10.0, threshold_session2=7.0, computed_by=None):
        execute_query("""
            INSERT INTO student_session_results
                (student_id, class_id, session_name, academic_year,
                 average, rank, decision, threshold_admis, threshold_session2,
                 computed_at, computed_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)
            ON CONFLICT (student_id, session_name, academic_year) DO UPDATE
                SET average             = EXCLUDED.average,
                    rank                = EXCLUDED.rank,
                    decision            = EXCLUDED.decision,
                    threshold_admis     = EXCLUDED.threshold_admis,
                    threshold_session2  = EXCLUDED.threshold_session2,
                    computed_at         = NOW(),
                    computed_by         = EXCLUDED.computed_by
        """, (student_id, class_id, session_name, academic_year,
              average, rank, decision,
              threshold_admis, threshold_session2, computed_by), fetch="none")

    @staticmethod
    def get_by_class_session(class_id, session_name):
        return execute_query("""
            SELECT ssr.*, s.full_name AS student_name, s.student_number
            FROM student_session_results ssr
            JOIN students s ON ssr.student_id = s.id
            WHERE ssr.class_id=%s AND ssr.session_name=%s
            ORDER BY ssr.rank NULLS LAST
        """, (class_id, session_name))

    @staticmethod
    def get_by_student(student_id):
        return execute_query("""
            SELECT * FROM student_session_results
            WHERE student_id=%s
            ORDER BY academic_year DESC, session_name
        """, (student_id,))

    @staticmethod
    def get_by_student_session(student_id, session_name):
        return execute_query("""
            SELECT * FROM student_session_results
            WHERE student_id=%s AND session_name=%s
            ORDER BY computed_at DESC
            LIMIT 1
        """, (student_id, session_name), fetch="one")


# ============================================================
# UNITÉS D'ENSEIGNEMENT (UE)
# ============================================================
class UEQueries:

    @staticmethod
    def get_by_department(department_id):
        return execute_query("""
            SELECT ue.*,
                   COUNT(c.id) FILTER (WHERE c.is_active)              AS ec_count,
                   COALESCE(SUM(c.credits_ec) FILTER (WHERE c.is_active), 0) AS total_ec_credits
            FROM unites_enseignement ue
            LEFT JOIN courses c ON c.ue_id = ue.id
            WHERE ue.department_id = %s AND ue.is_active = TRUE
            GROUP BY ue.id
            ORDER BY ue.group_label, ue.code NULLS LAST, ue.name
        """, (department_id,))

    @staticmethod
    def get_by_promotion(promotion_id):
        """UEs spécifiques à la promotion + UEs partagées (sans promotion)."""
        return execute_query("""
            SELECT ue.*,
                   COUNT(c.id) FILTER (WHERE c.is_active)              AS ec_count,
                   COALESCE(SUM(c.credits_ec) FILTER (WHERE c.is_active), 0) AS total_ec_credits
            FROM unites_enseignement ue
            LEFT JOIN courses c ON c.ue_id = ue.id
            WHERE (ue.promotion_id = %s OR ue.promotion_id IS NULL)
              AND ue.is_active = TRUE
            GROUP BY ue.id
            ORDER BY ue.group_label, ue.code NULLS LAST, ue.name
        """, (promotion_id,))

    @staticmethod
    def get_by_id(ue_id):
        return execute_query(
            "SELECT * FROM unites_enseignement WHERE id=%s",
            (ue_id,), fetch="one"
        )

    @staticmethod
    def create(department_id, name, code, credits, group_label="A", promotion_id=None):
        return execute_query("""
            INSERT INTO unites_enseignement
                (department_id, name, code, credits, group_label, promotion_id)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
        """, (department_id, name, code or None,
              credits, group_label or "A", promotion_id), fetch="one")

    @staticmethod
    def update(ue_id, name, code, credits, group_label="A"):
        execute_query("""
            UPDATE unites_enseignement
            SET name=%s, code=%s, credits=%s, group_label=%s
            WHERE id=%s
        """, (name, code or None, credits,
              group_label or "A", ue_id), fetch="none")

    @staticmethod
    def delete(ue_id):
        execute_query(
            "UPDATE unites_enseignement SET is_active=FALSE WHERE id=%s",
            (ue_id,), fetch="none"
        )

    @staticmethod
    def assign_course(course_id, ue_id, credits_ec=1.0):
        execute_query(
            "UPDATE courses SET ue_id=%s, credits_ec=%s WHERE id=%s",
            (ue_id, credits_ec, course_id), fetch="none"
        )

    @staticmethod
    def unassign_course(course_id):
        execute_query(
            "UPDATE courses SET ue_id=NULL, credits_ec=1 WHERE id=%s",
            (course_id,), fetch="none"
        )


# ============================================================
# RÉSULTATS PAR UE PAR ÉTUDIANT
# ============================================================
class StudentUEResultsQueries:

    @staticmethod
    def upsert(student_id, ue_id, session_name, academic_year,
               note_ue, credits_obtained, decision, computed_by=None):
        execute_query("""
            INSERT INTO student_ue_results
                (student_id, ue_id, session_name, academic_year,
                 note_ue, credits_obtained, decision, computed_at, computed_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),%s)
            ON CONFLICT (student_id, ue_id, session_name, academic_year) DO UPDATE
                SET note_ue          = EXCLUDED.note_ue,
                    credits_obtained = EXCLUDED.credits_obtained,
                    decision         = EXCLUDED.decision,
                    computed_at      = NOW(),
                    computed_by      = EXCLUDED.computed_by
        """, (student_id, ue_id, session_name, academic_year,
              note_ue, credits_obtained, decision, computed_by), fetch="none")

    @staticmethod
    def get_by_student_session(student_id, session_name):
        return execute_query("""
            SELECT sur.*,
                   ue.name        AS ue_name,
                   ue.code        AS ue_code,
                   ue.credits     AS ue_credits,
                   ue.group_label AS ue_group
            FROM student_ue_results sur
            JOIN unites_enseignement ue ON sur.ue_id = ue.id
            WHERE sur.student_id = %s AND sur.session_name = %s
            ORDER BY ue.group_label, ue.code NULLS LAST
        """, (student_id, session_name))


# ============================================================
# DÉLIBÉRATIONS ANNUELLES
# ============================================================
class DeliberationAnnuelleQueries:

    @staticmethod
    def upsert(student_id, class_id, academic_year, moy_s1, moy_s2,
               moy_annuelle, credits_obtenus, credits_total,
               ecs_a_reprendre, decision):
        execute_query("""
            INSERT INTO deliberations_annuelles
                (student_id, class_id, academic_year, moy_s1, moy_s2,
                 moy_annuelle, credits_obtenus, credits_total,
                 ecs_a_reprendre, decision, published, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE,NOW())
            ON CONFLICT (student_id, class_id, academic_year) DO UPDATE SET
                moy_s1          = EXCLUDED.moy_s1,
                moy_s2          = EXCLUDED.moy_s2,
                moy_annuelle    = EXCLUDED.moy_annuelle,
                credits_obtenus = EXCLUDED.credits_obtenus,
                credits_total   = EXCLUDED.credits_total,
                ecs_a_reprendre = EXCLUDED.ecs_a_reprendre,
                decision        = EXCLUDED.decision,
                published       = FALSE,
                updated_at      = NOW()
        """, (student_id, class_id, academic_year, moy_s1, moy_s2,
              moy_annuelle, credits_obtenus, credits_total,
              ecs_a_reprendre, decision), fetch="none")

    @staticmethod
    def publish(class_id, academic_year, published_by):
        execute_query("""
            UPDATE deliberations_annuelles
            SET published=TRUE, published_at=NOW(), published_by=%s
            WHERE class_id=%s AND academic_year=%s
        """, (published_by, class_id, academic_year), fetch="none")

    @staticmethod
    def get_by_class(class_id, academic_year):
        return execute_query("""
            SELECT da.*, s.full_name AS student_name, s.student_number
            FROM deliberations_annuelles da
            JOIN students s ON da.student_id = s.id
            WHERE da.class_id=%s AND da.academic_year=%s
            ORDER BY da.moy_annuelle DESC NULLS LAST
        """, (class_id, academic_year))

    @staticmethod
    def get_published_years_by_student(student_id):
        """Années académiques pour lesquelles une délibération publiée existe."""
        return execute_query("""
            SELECT academic_year FROM deliberations_annuelles
            WHERE student_id=%s AND published=TRUE
            ORDER BY academic_year DESC
        """, (student_id,))

    @staticmethod
    def get_by_student_year(student_id, academic_year):
        return execute_query("""
            SELECT * FROM deliberations_annuelles
            WHERE student_id=%s AND academic_year=%s AND published=TRUE
        """, (student_id, academic_year), fetch="one")

    @staticmethod
    def get_by_class_session(class_id, session_name):
        return execute_query("""
            SELECT sur.*,
                   s.full_name AS student_name, s.student_number,
                   ue.name AS ue_name, ue.code AS ue_code,
                   ue.credits AS ue_credits, ue.group_label AS ue_group
            FROM student_ue_results sur
            JOIN students s ON sur.student_id = s.id
            JOIN unites_enseignement ue ON sur.ue_id = ue.id
            WHERE s.class_id = %s AND sur.session_name = %s
            ORDER BY s.full_name, ue.group_label, ue.code NULLS LAST
        """, (class_id, session_name))


# ============================================================
# ANNÉES ACADÉMIQUES
# ============================================================
class AcademicYearQueries:

    @staticmethod
    def get_by_university(university_id):
        return execute_query("""
            SELECT * FROM academic_years
            WHERE university_id = %s
            ORDER BY label DESC
        """, (university_id,))

    @staticmethod
    def get_current(university_id):
        return execute_query("""
            SELECT * FROM academic_years
            WHERE university_id = %s AND is_current = TRUE
            LIMIT 1
        """, (university_id,), fetch="one")

    @staticmethod
    def get_by_id(year_id):
        return execute_query(
            "SELECT * FROM academic_years WHERE id = %s",
            (year_id,), fetch="one"
        )

    @staticmethod
    def create(university_id, label, start_date=None, end_date=None,
               notes=None, status="active"):
        return execute_query("""
            INSERT INTO academic_years
                (university_id, label, start_date, end_date, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (university_id, label, start_date or None, end_date or None,
              notes or None, status), fetch="one")

    @staticmethod
    def set_current(year_id, university_id):
        """Définit une année comme courante (désactive les autres pour cette université)."""
        execute_query("""
            UPDATE academic_years
            SET is_current = FALSE
            WHERE university_id = %s
        """, (university_id,), fetch="none")
        execute_query("""
            UPDATE academic_years
            SET is_current = TRUE
            WHERE id = %s
        """, (year_id,), fetch="none")

    @staticmethod
    def set_status(year_id, status):
        execute_query("""
            UPDATE academic_years SET status = %s WHERE id = %s
        """, (status, year_id), fetch="none")

    @staticmethod
    def update(year_id, label, start_date=None, end_date=None, notes=None):
        execute_query("""
            UPDATE academic_years
            SET label=%s, start_date=%s, end_date=%s, notes=%s
            WHERE id=%s
        """, (label, start_date or None, end_date or None,
              notes or None, year_id), fetch="none")
