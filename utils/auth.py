# utils/auth.py
import bcrypt
import streamlit as st
from db.queries import UserQueries

ROLE_LABELS = {
    "super_admin":       "Super Administrateur",
    "admin_universite":  "Admin Université",
    "admin_faculte":     "Admin Faculté",
    "admin_departement": "Admin Département",
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
