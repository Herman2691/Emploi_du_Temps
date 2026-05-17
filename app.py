import streamlit as st

st.set_page_config(
    page_title="UniSchedule",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.components import inject_global_css
from utils.auth import get_current_user, get_current_student, logout, logout_student

inject_global_css()
user    = get_current_user()
student = get_current_student()

# ── Construction des pages (toutes toujours enregistrées pour éviter "Page not found") ──

_is_prof  = user and (str(user.get("role","")).strip().lower() == "professeur"
                      or user.get("professor_id") is not None)
_is_admin = user and not _is_prof

# Déterminer la page par défaut
if _is_prof:
    _default_page = "pages/9_Prof_Dashboard.py"
elif _is_admin:
    _default_page = "pages/8_Admin_Dashboard.py"
elif student:
    _default_page = "pages/11_Student_Dashboard.py"
else:
    _default_page = "pages/1_Accueil.py"

def _pg(path, title, icon):
    return st.Page(path, title=title, icon=icon,
                   default=(path == _default_page))

all_pages = {
    "🌐 Espace Public": [
        _pg("pages/1_Accueil.py",             "Accueil",           "🏠"),
        _pg("pages/2_Horaire.py",             "Emploi du Temps",   "📅"),
    ],
    "🎓 Espace Étudiant": [
        _pg("pages/10_Student_Auth.py",       "Espace Étudiant",   "🎓"),
        _pg("pages/11_Student_Dashboard.py",  "Mon Espace",        "📚"),
    ],
    "👨‍🏫 Espace Professeur": [
        _pg("pages/12_Prof_Auth.py",          "Connexion Prof",    "👨‍🏫"),
        _pg("pages/9_Prof_Dashboard.py",      "Mon Espace Prof",   "📖"),
    ],
    "⚙️ Administration": [
        _pg("pages/7_Admin_Login.py",         "Connexion Admin",   "🔑"),
        _pg("pages/8_Admin_Dashboard.py",     "Dashboard Admin",   "📊"),
    ],
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 0.25rem">
        <h2 style="margin:0;font-family:'Poppins',sans-serif;color:#1E293B;font-size:1.4rem">
            🎓 UniSchedule
        </h2>
        <p style="margin:0;color:#64748B;font-size:0.78rem">Emplois du temps universitaires</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if user:
        role_labels = {
            "super_admin":       ("🔴", "Super Admin"),
            "admin_universite":  ("🔵", "Admin Université"),
            "admin_faculte":     ("🟢", "Admin Faculté"),
            "admin_departement": ("🟡", "Admin Département"),
            "professeur":        ("🟣", "Professeur"),
        }
        icon_r, label_r = role_labels.get(user["role"], ("⚪", user["role"]))
        st.markdown(f"""
        <div style="background:#F1F5F9;border-radius:8px;padding:0.6rem 0.8rem;margin-bottom:0.75rem">
            <div style="font-weight:600;color:#1E293B;font-size:0.9rem">👤 {user['name']}</div>
            <div style="color:#64748B;font-size:0.78rem">{icon_r} {label_r}</div>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Se déconnecter", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
        st.divider()

    elif student:
        _stu_username = student.get("username") or student["student_number"]
        _stu_name     = student.get("display_name") or student.get("full_name","Étudiant")
        st.markdown(f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                    padding:0.6rem 0.8rem;margin-bottom:0.75rem">
            <div style="font-weight:600;color:#065F46;font-size:0.9rem">
                🎓 {_stu_name}
            </div>
            <div style="color:#6B7280;font-size:0.75rem;margin-top:2px">
                @{_stu_username} · N° {student['student_number']}
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Se déconnecter", use_container_width=True, type="secondary"):
            logout_student()
            st.rerun()
        st.divider()

    st.caption("© 2025 UniSchedule v2.0")

pg = st.navigation(all_pages)
pg.run()
