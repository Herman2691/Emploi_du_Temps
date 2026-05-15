# utils/auth.py
import bcrypt
import streamlit as st
from db.queries import UserQueries, StudentQueries, StudentRegistryQueries

ROLE_LABELS = {
    "super_admin":       "Super Administrateur",
    "admin_universite":  "Admin Université",
    "admin_faculte":     "Admin Faculté",
    "admin_departement": "Admin Département",
    "professeur":        "Professeur",
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def login(email: str, password: str):
    if not email or not password:
        return False, "Email et mot de passe requis."
    try:
        user = UserQueries.get_by_email(email.strip())
    except Exception as e:
        return False, f"Erreur de connexion : {e}"

    if not user:
        return False, "Identifiants incorrects."
    if not verify_password(password, user["password_hash"]):
        return False, "Identifiants incorrects."
    if not user.get("is_active"):
        return False, "Ce compte est désactivé."

    st.session_state["user"] = {
        "id":            user["id"],
        "name":          user["name"],
        "email":         user["email"],
        "role":          user["role"],
        "university_id": user.get("university_id"),
        "faculty_id":    user.get("faculty_id"),
        "department_id": user.get("department_id"),
        "professor_id":  user.get("professor_id"),
    }
    st.session_state["authenticated"] = True

    try:
        UserQueries.update_last_login(user["id"])
    except Exception:
        pass  # non bloquant

    return True, f"Bienvenue, {user['name']} !"


def logout():
    for key in ["user", "authenticated"]:
        st.session_state.pop(key, None)


def get_current_user():
    if st.session_state.get("authenticated") and "user" in st.session_state:
        return st.session_state["user"]
    return None


def is_authenticated() -> bool:
    return bool(get_current_user())


def get_role():
    user = get_current_user()
    return user["role"] if user else None


def has_role(*roles: str) -> bool:
    return get_role() in roles


def require_auth():
    """Redirige vers login si non authentifié."""
    if not is_authenticated():
        st.warning("🔒 Accès restreint. Veuillez vous connecter.")
        if st.button("→ Se connecter", type="primary"):
            st.switch_page("pages/7_Admin_Login.py")
        st.stop()


def require_prof_auth():
    """Redirige vers login si pas connecté en tant que professeur."""
    user = get_current_user()
    if not user or user.get("role") != "professeur":
        st.warning("🔒 Accès réservé aux professeurs.")
        if st.button("→ Se connecter", type="primary"):
            st.switch_page("pages/12_Prof_Auth.py")
        st.stop()


# ════════════════════════════════════════════════════════════
# AUTH ÉTUDIANTS  (session séparée : st.session_state["student"])
# ════════════════════════════════════════════════════════════

def get_current_student():
    if st.session_state.get("student_authenticated") and "student" in st.session_state:
        return st.session_state["student"]
    return None


def logout_student():
    for k in ["student", "student_authenticated"]:
        st.session_state.pop(k, None)


def require_student_auth():
    if not get_current_student():
        st.warning("🔒 Veuillez vous connecter à votre espace étudiant.")
        if st.button("→ Se connecter / S'inscrire", type="primary"):
            st.switch_page("pages/10_Student_Auth.py")
        st.stop()


def login_student(login_input: str, university_id: int, password: str):
    if not login_input or not password:
        return False, "Identifiant et mot de passe requis."
    try:
        student = StudentQueries.get_by_login(login_input, university_id)
    except Exception as e:
        return False, f"Erreur de connexion : {e}"

    if not student:
        return False, "Identifiant ou mot de passe incorrect."
    if not verify_password(password, student["password_hash"]):
        return False, "Identifiant ou mot de passe incorrect."
    if not student.get("is_active"):
        return False, "Ce compte étudiant est désactivé."

    prenom = student.get("prenom") or ""
    nom    = student.get("nom") or student.get("full_name") or ""
    display_name = f"{prenom} {nom}".strip() or student.get("full_name", "")

    st.session_state["student"] = {
        "id":             student["id"],
        "student_number": student["student_number"],
        "full_name":      student.get("full_name") or display_name,
        "display_name":   display_name,
        "nom":            student.get("nom"),
        "postnom":        student.get("postnom"),
        "prenom":         student.get("prenom"),
        "username":       student.get("username"),
        "email":          student.get("email"),
        "class_id":       student.get("class_id"),
        "university_id":  student["university_id"],
    }
    st.session_state["student_authenticated"] = True

    try:
        StudentQueries.update_last_login(student["id"])
    except Exception:
        pass

    return True, f"Bienvenue, {display_name or student['student_number']} !"


def login_unified(identifier: str, password: str):
    """Connexion unifiée : essaie admin/prof puis étudiant.
    Retourne (success, message, user_type) où user_type est 'admin' ou 'student'."""
    if not identifier or not password:
        return False, "Identifiant et mot de passe requis.", None

    # Essai admin/prof
    success, msg = login(identifier.strip(), password)
    if success:
        return True, msg, "admin"

    # Essai étudiant (toutes universités)
    try:
        student = StudentQueries.get_by_login_global(identifier)
    except Exception as e:
        return False, f"Erreur de connexion : {e}", None

    if not student:
        return False, "Identifiant ou mot de passe incorrect.", None
    if not verify_password(password, student["password_hash"]):
        return False, "Identifiant ou mot de passe incorrect.", None
    if not student.get("is_active"):
        return False, "Ce compte est désactivé.", None

    prenom = student.get("prenom") or ""
    nom    = student.get("nom") or student.get("full_name") or ""
    display_name = f"{prenom} {nom}".strip() or student.get("full_name", "")

    st.session_state["student"] = {
        "id":             student["id"],
        "student_number": student["student_number"],
        "full_name":      student.get("full_name") or display_name,
        "display_name":   display_name,
        "nom":            student.get("nom"),
        "postnom":        student.get("postnom"),
        "prenom":         student.get("prenom"),
        "username":       student.get("username"),
        "email":          student.get("email"),
        "class_id":       student.get("class_id"),
        "university_id":  student["university_id"],
    }
    st.session_state["student_authenticated"] = True

    try:
        StudentQueries.update_last_login(student["id"])
    except Exception:
        pass

    return True, f"Bienvenue, {display_name or student['student_number']} !", "student"


def register_student(student_number: str, university_id: int,
                     username: str, password: str, confirm: str):
    if not student_number or not username or not password:
        return False, "Tous les champs obligatoires doivent être remplis."
    if len(username.strip()) < 3:
        return False, "Le nom d'utilisateur doit contenir au moins 3 caractères."
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if password != confirm:
        return False, "Les mots de passe ne correspondent pas."

    try:
        registry = StudentRegistryQueries.verify(student_number, university_id)
    except Exception as e:
        return False, f"Erreur de vérification : {e}"

    if not registry:
        return False, "Numéro étudiant non reconnu pour cette université. Contactez l'administration."

    try:
        existing = StudentQueries.exists(student_number, university_id)
    except Exception as e:
        return False, f"Erreur : {e}"
    if existing:
        return False, "Un compte existe déjà pour ce numéro étudiant."

    try:
        taken = StudentQueries.exists_username(username.strip())
    except Exception as e:
        return False, f"Erreur : {e}"
    if taken:
        return False, "Ce nom d'utilisateur est déjà pris. Choisissez-en un autre."

    nom     = registry.get("nom") or ""
    postnom = registry.get("postnom") or ""
    prenom  = registry.get("prenom") or ""
    full_name = " ".join(filter(None, [prenom, nom, postnom])) or registry.get("full_name", "")

    try:
        pwd_hash = hash_password(password)
        StudentQueries.create(
            student_number=student_number,
            full_name=full_name,
            email=registry.get("email"),
            password_hash=pwd_hash,
            class_id=registry.get("class_id"),
            university_id=university_id,
            registry_id=registry["id"],
            nom=nom or None,
            postnom=postnom or None,
            prenom=prenom or None,
            username=username.strip(),
        )
        StudentRegistryQueries.mark_registered(registry["id"])
        return True, f"Compte créé ! Connectez-vous avec le nom d'utilisateur : {username.strip()}"
    except Exception as e:
        return False, f"Erreur lors de la création : {e}"


def change_student_password(student_id: int, current_password: str,
                            new_password: str, confirm: str):
    if not current_password or not new_password:
        return False, "Tous les champs sont obligatoires."
    if len(new_password) < 8:
        return False, "Le nouveau mot de passe doit contenir au moins 8 caractères."
    if new_password != confirm:
        return False, "Les mots de passe ne correspondent pas."

    try:
        student = StudentQueries.get_by_id(student_id)
    except Exception as e:
        return False, f"Erreur : {e}"

    if not student:
        return False, "Compte introuvable."
    if not verify_password(current_password, student["password_hash"]):
        return False, "Mot de passe actuel incorrect."

    try:
        StudentQueries.reset_password(student_id, hash_password(new_password))
        return True, "Mot de passe modifié avec succès."
    except Exception as e:
        return False, f"Erreur lors de la modification : {e}"


def create_admin(name, email, password, role,
                 university_id=None, faculty_id=None, department_id=None):
    if not name or not name.strip():
        return False, "Le nom est obligatoire."
    if not email or "@" not in email:
        return False, "Email invalide."
    if not password or len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."

    try:
        existing = UserQueries.get_by_email(email.strip())
    except Exception as e:
        return False, f"Erreur vérification email : {e}"

    if existing:
        return False, "Cet email est déjà utilisé."

    try:
        password_hash = hash_password(password)
        result = UserQueries.create(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            university_id=university_id,
            faculty_id=faculty_id,
            department_id=department_id,
        )
        if result:
            return True, f"Admin '{name.strip()}' créé avec succès."
        return False, "Erreur lors de la création."
    except Exception as e:
        return False, f"Erreur : {e}"
