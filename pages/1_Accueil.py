# pages/1_Accueil.py
import streamlit as st
from utils.auth import get_current_user, get_current_student, login_unified
from utils.components import inject_global_css, auth_page_css
from db.queries import UniversityQueries

user    = get_current_user()
student = get_current_student()

# ══════════════════════════════════════════════════════════════════════════════
# CONNECTÉ — Admin / Prof
# ══════════════════════════════════════════════════════════════════════════════
if user:
    inject_global_css()
    uni_id   = user.get("university_id")
    uni_name = ""
    uni_color = "#2563EB"
    if uni_id:
        try:
            uni = UniversityQueries.get_by_id(uni_id)
            if uni:
                uni_name  = uni.get("name", "")
                uni_color = uni.get("primary_color") or "#2563EB"
        except Exception:
            pass

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{uni_color}dd,{uni_color}99);
                border-radius:18px;padding:2rem 2.5rem;color:white;margin-bottom:1.5rem">
        <h2 style="margin:0;font-family:'Poppins',sans-serif;font-size:1.8rem">
            🎓 {uni_name or "UniSchedule"}
        </h2>
        <p style="margin:0.4rem 0 0;opacity:0.85;font-size:0.9rem">
            Bienvenue, <strong>{user['name']}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 Mon Tableau de Bord", type="primary", use_container_width=True):
            if user.get("role") == "professeur":
                st.switch_page("pages/9_Prof_Dashboard.py")
            else:
                st.switch_page("pages/8_Admin_Dashboard.py")
    with c2:
        if st.button("📅 Voir l'emploi du temps", use_container_width=True):
            st.switch_page("pages/2_Horaire.py")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# CONNECTÉ — Étudiant
# ══════════════════════════════════════════════════════════════════════════════
if student:
    st.switch_page("pages/11_Student_Dashboard.py")

# ══════════════════════════════════════════════════════════════════════════════
# NON CONNECTÉ — Page de connexion unifiée
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(auth_page_css("#2563EB", "#1D4ED8"), unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
    background: white;
    border: 1.5px solid #E2E8F0;
    border-radius: 22px;
    padding: 2.5rem 2rem 2rem !important;
    box-shadow: 0 8px 32px rgba(37,99,235,0.09), 0 2px 8px rgba(0,0,0,0.04);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)

_, col, _ = st.columns([1, 1.4, 1])

with col:
    st.markdown("""
<div style="text-align:center;margin-bottom:1.8rem">
    <div style="width:72px;height:72px;
                background:linear-gradient(135deg,#2563EB,#1D4ED8);
                border-radius:20px;margin:0 auto 1rem;
                display:flex;align-items:center;justify-content:center;
                font-size:2.2rem;
                box-shadow:0 6px 22px rgba(37,99,235,0.28)">🎓</div>
    <h2 style="color:#1E293B;font-family:'Poppins',sans-serif;
               font-size:1.6rem;font-weight:700;margin:0;line-height:1.2">
        UniSchedule
    </h2>
    <p style="color:#64748B;font-size:0.82rem;margin:0.4rem 0 0">
        Connectez-vous pour accéder à votre espace
    </p>
</div>
""", unsafe_allow_html=True)

    identifier = st.text_input(
        "Email ou matricule étudiant",
        placeholder="ex: admin@univ.cd  ou  ETU2024001",
        key="unified_id"
    )
    password = st.text_input(
        "Mot de passe",
        placeholder="••••••••",
        type="password",
        key="unified_pw"
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if st.button("→  Se connecter", type="primary", use_container_width=True):
        if not identifier or not password:
            st.error("Veuillez renseigner vos identifiants.")
        else:
            with st.spinner("Authentification..."):
                success, message, user_type = login_unified(identifier.strip(), password)
            if success:
                st.rerun()
            else:
                st.error(f"❌ {message}")

    st.markdown("""
<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0">
    <div style="flex:1;height:1px;background:#E2E8F0"></div>
    <span style="color:#94A3B8;font-size:0.75rem">ou</span>
    <div style="flex:1;height:1px;background:#E2E8F0"></div>
</div>
""", unsafe_allow_html=True)

    if st.button("📅  Voir l'emploi du temps sans connexion",
                 use_container_width=True, type="secondary"):
        st.switch_page("pages/2_Horaire.py")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if st.button("📝  Créer un compte étudiant",
                 use_container_width=True):
        st.switch_page("pages/10_Student_Auth.py")

    st.markdown("""
<div style="text-align:center;margin-top:1.5rem">
    <p style="color:#94A3B8;font-size:0.68rem">
        🎓 UniSchedule · © 2025 · Toutes les tentatives sont enregistrées
    </p>
</div>
""", unsafe_allow_html=True)
