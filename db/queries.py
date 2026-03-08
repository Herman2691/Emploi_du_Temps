# db/queries.py
from db.connection import execute_query


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
    def create(name, address, photo_url, website):
        return execute_query(
            "INSERT INTO universities (name,address,photo_url,website) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, address or None, photo_url or None, website or None), fetch="one"
        )

    @staticmethod
    def update(university_id, name, address, photo_url, website):
        execute_query(
            "UPDATE universities SET name=%s,address=%s,photo_url=%s,website=%s WHERE id=%s",
            (name, address or None, photo_url or None, website or None, university_id), fetch="none"
        )

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
    def get_by_faculty(faculty_id):
        return execute_query(
            "SELECT * FROM departments WHERE faculty_id=%s AND is_active=TRUE ORDER BY name",
            (faculty_id,)
        )

    @staticmethod
    def get_by_id(department_id):
        return execute_query(
            "SELECT d.*, f.name AS faculty_name, u.name AS university_name "
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
    def create(name, academic_year, department_id):
        return execute_query(
            "INSERT INTO promotions (name,academic_year,department_id) VALUES (%s,%s,%s) RETURNING id",
            (name, academic_year, department_id), fetch="one"
        )

    @staticmethod
    def update(promotion_id, name, academic_year):
        execute_query(
            "UPDATE promotions SET name=%s,academic_year=%s WHERE id=%s",
            (name, academic_year, promotion_id), fetch="none"
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
    def get_by_department(department_id):
        return execute_query(
            "SELECT * FROM professors WHERE department_id=%s AND is_active=TRUE ORDER BY name",
            (department_id,)
        )

    @staticmethod
    def get_by_id(professor_id):
        return execute_query(
            "SELECT * FROM professors WHERE id=%s",
            (professor_id,), fetch="one"
        )

    @staticmethod
    def create(name, email, phone, department_id):
        return execute_query(
            "INSERT INTO professors (name,email,phone,department_id) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, email or None, phone or None, department_id), fetch="one"
        )

    @staticmethod
    def update(professor_id, name, email, phone):
        execute_query(
            "UPDATE professors SET name=%s,email=%s,phone=%s WHERE id=%s",
            (name, email or None, phone or None, professor_id), fetch="none"
        )

    @staticmethod
    def delete(professor_id):
        execute_query("UPDATE professors SET is_active=FALSE WHERE id=%s",
                      (professor_id,), fetch="none")


# ============================================================
# COURS
# ============================================================
class CourseQueries:

    @staticmethod
    def get_by_department(department_id):
        return execute_query(
            "SELECT * FROM courses WHERE department_id=%s AND is_active=TRUE ORDER BY name",
            (department_id,)
        )

    @staticmethod
    def get_by_class(class_id):
        """
        Cours d'une classe : d'abord via les horaires, puis
        tous les cours du département si aucun horaire encore planifié.
        """
        courses = execute_query("""
            SELECT DISTINCT c.* FROM courses c
            JOIN schedules s ON s.course_id=c.id
            WHERE s.class_id=%s AND s.is_active=TRUE AND c.is_active=TRUE
            ORDER BY c.name
        """, (class_id,))
        # Fallback : retourne les cours du département si aucun horaire
        if not courses:
            courses = execute_query("""
                SELECT c.* FROM courses c
                JOIN departments d  ON c.department_id=d.id
                JOIN promotions pr  ON pr.department_id=d.id
                JOIN classes cl     ON cl.promotion_id=pr.id
                WHERE cl.id=%s AND c.is_active=TRUE
                ORDER BY c.name
            """, (class_id,))
        return courses or []

    @staticmethod
    def get_by_id(course_id):
        return execute_query(
            "SELECT * FROM courses WHERE id=%s",
            (course_id,), fetch="one"
        )

    @staticmethod
    def create(name, code, hours, weight, department_id):
        return execute_query(
            "INSERT INTO courses (name,code,hours,weight,department_id) VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (name, code or None, hours, weight, department_id), fetch="one"
        )

    @staticmethod
    def update(course_id, name, code, hours, weight):
        execute_query(
            "UPDATE courses SET name=%s,code=%s,hours=%s,weight=%s WHERE id=%s",
            (name, code or None, hours, weight, course_id), fetch="none"
        )

    @staticmethod
    def delete(course_id):
        execute_query("UPDATE courses SET is_active=FALSE WHERE id=%s",
                      (course_id,), fetch="none")


# ============================================================
# EMPLOIS DU TEMPS
# ============================================================
class ScheduleQueries:

    @staticmethod
    def get_by_class(class_id):
        return execute_query("""
            SELECT s.*,
                   c.name  AS course_name,  c.code AS course_code,
                   p.name  AS professor_name,
                   cl.name AS class_name
            FROM schedules s
            JOIN courses    c  ON s.course_id=c.id
            JOIN professors p  ON s.professor_id=p.id
            JOIN classes    cl ON s.class_id=cl.id
            WHERE s.class_id=%s AND s.is_active=TRUE
            ORDER BY
                CASE s.day
                    WHEN 'Lundi'    THEN 1 WHEN 'Mardi'   THEN 2
                    WHEN 'Mercredi' THEN 3 WHEN 'Jeudi'   THEN 4
                    WHEN 'Vendredi' THEN 5 WHEN 'Samedi'  THEN 6
                END, s.start_time
        """, (class_id,))

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
    def create(class_id, day, start_time, end_time, room, course_id, professor_id, week_type="Toutes"):
        return execute_query("""
            INSERT INTO schedules
                (class_id,day,start_time,end_time,room,course_id,professor_id,week_type)
            VALUES (%s,%s,%s::time,%s::time,%s,%s,%s,%s) RETURNING id
        """, (class_id, day, start_time, end_time, room or None,
              course_id, professor_id, week_type), fetch="one")

    @staticmethod
    def update(schedule_id, day, start_time, end_time, room, course_id, professor_id, week_type):
        execute_query("""
            UPDATE schedules SET day=%s,start_time=%s::time,end_time=%s::time,
            room=%s,course_id=%s,professor_id=%s,week_type=%s WHERE id=%s
        """, (day, start_time, end_time, room or None,
              course_id, professor_id, week_type, schedule_id), fetch="none")

    @staticmethod
    def delete(schedule_id):
        execute_query("UPDATE schedules SET is_active=FALSE WHERE id=%s",
                      (schedule_id,), fetch="none")


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
    def create(title, content, department_id, is_pinned=False, expires_at=None):
        return execute_query("""
            INSERT INTO announcements (title,content,department_id,is_pinned,expires_at)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (title, content, department_id, is_pinned, expires_at), fetch="one")

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
