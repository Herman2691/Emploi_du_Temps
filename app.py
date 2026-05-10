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

# ── Construction dynamique des pages selon l'état de connexion ─────────────────

_is_prof = user and (
    str(user.get("role", "")).strip().lower() == "professeur"
    or user.get("professor_id") is not None
)
_is_admin = user and not _is_prof

if _is_prof:
    # Professeur → Accueil + Horaire + son espace uniquement
    all_pages = {
        "🌐 Espace Public": [
            st.Page("pages/1_Accueil.py",         title="Accueil",         icon="🏠"),
            st.Page("pages/2_Horaire.py",         title="Mon Horaire",     icon="📅"),
        ],
        "👨‍🏫 Espace Professeur": [
            st.Page("pages/9_Prof_Dashboard.py",  title="Mon Espace Prof", icon="📖", default=True),
        ],
    }

elif _is_admin:
    # Admin (toute hiérarchie) → tout visible
    all_pages = {
        "🌐 Espace Public": [
            st.Page("pages/1_Accueil.py",          title="Accueil",           icon="🏠"),
            st.Page("pages/2_Horaire.py",          title="Mon Horaire",       icon="📅"),
        ],
        "🎓 Espace Étudiant": [
            st.Page("pages/10_Student_Auth.py",    title="Espace Étudiant",   icon="🎓"),
            st.Page("pages/11_Student_Dashboard.py", title="Mon Espace",      icon="📚"),
        ],
        "👨‍🏫 Espace Professeur": [
            st.Page("pages/12_Prof_Auth.py",       title="Espace Professeur", icon="👨‍🏫"),
        ],
        "⚙️ Administration": [
            st.Page("pages/8_Admin_Dashboard.py",  title="Dashboard Admin",   icon="📊", default=True),
        ],
    }

elif student:
    # Étudiant → Accueil + Horaire + son espace uniquement
    all_pages = {
        "🌐 Espace Public": [
            st.Page("pages/1_Accueil.py",          title="Accueil",         icon="🏠"),
            st.Page("pages/2_Horaire.py",          title="Mon Horaire",     icon="📅"),
        ],
        "🎓 Espace Étudiant": [
            st.Page("pages/10_Student_Auth.py",    title="Espace Étudiant", icon="🎓"),
            st.Page("pages/11_Student_Dashboard.py", title="Mon Espace",    icon="📚", default=True),
        ],
    }

else:
    # Non connecté → Login unifié + Horaire public
    all_pages = {
        "🌐 Espace Public": [
            st.Page("pages/1_Accueil.py",          title="Connexion",        icon="🔑", default=True),
            st.Page("pages/2_Horaire.py",          title="Emploi du Temps",  icon="📅"),
        ],
        "🎓 Espace Étudiant": [
            st.Page("pages/10_Student_Auth.py",    title="Créer un compte",  icon="📝"),
            st.Page("pages/11_Student_Dashboard.py", title="Mon Espace",     icon="📚"),
        ],
        "👨‍🏫 Espace Professeur": [
            st.Page("pages/12_Prof_Auth.py",       title="Espace Professeur", icon="👨‍🏫"),
        ],
        "⚙️ Administration": [
            st.Page("pages/7_Admin_Login.py",      title="Connexion Admin",   icon="🔑"),
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
