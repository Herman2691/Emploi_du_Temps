# utils/role_guard.py
import streamlit as st
from utils.auth import get_current_user, is_authenticated

def require_role(*allowed_roles: str):
    """Arrête la page si le rôle n'est pas autorisé."""
    user = get_current_user()
    if not user or user["role"] not in allowed_roles:
        st.error("⛔ Accès non autorisé.")
        st.stop()

def scope_check(user: dict, university_id=None, faculty_id=None, department_id=None) -> bool:
    """Vérifie que l'utilisateur a bien accès à la ressource demandée."""
    role = user.get("role")
    if role == "super_admin":
        return True
    if role == "admin_universite" and university_id:
        return user.get("university_id") == university_id
    if role == "admin_faculte" and faculty_id:
        return user.get("faculty_id") == faculty_id
    if role == "admin_departement" and department_id:
        return user.get("department_id") == department_id
    return False
