# pages/7_Admin_Login.py
"""
Page de connexion administrateur — Interface autonome et sécurisée.
Accessible uniquement via URL directe : localhost:8501/Admin_Login
Complètement séparée de l'espace étudiant — aucun lien depuis la sidebar.
"""

import streamlit as st
from utils.auth import login, is_authenticated, get_current_user
from utils.components import auth_page_css, auth_header

# Redirection si déjà connecté
if is_authenticated():
    u = get_current_user()
    if u and u.get("role") == "professeur":
        st.switch_page("pages/9_Prof_Dashboard.py")
    else:
        st.switch_page("pages/8_Admin_Dashboard.py")

st.markdown(auth_page_css("#2563EB", "#1D4ED8"), unsafe_allow_html=True)

# ── Layout centré ──────────────────────────────────────────────────────────────
st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)

_, col, _ = st.columns([1, 1.6, 1])

with col:
    auth_header("🔐", "Espace Administrateur",
                "Accès restreint · Personnel autorisé uniquement", "#2563EB")

    st.markdown("""
<div style="background:white;border:1px solid #E2E8F0;
            border-radius:18px;padding:2rem 2rem 1.5rem;
            box-shadow:0 4px 24px rgba(0,0,0,0.07),0 1px 4px rgba(0,0,0,0.04)">
""", unsafe_allow_html=True)

    email    = st.text_input("Adresse e-mail",  placeholder="admin@universite.dz",  key="adm_email")
    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
    password = st.text_input("Mot de passe",    placeholder="••••••••",
                              type="password",  key="adm_password")
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if st.button("→  Se connecter", type="primary", use_container_width=True):
        if not email or not password:
            st.error("Veuillez renseigner vos identifiants.")
        else:
            with st.spinner("Authentification..."):
                success, message = login(email.strip(), password)
            if success:
                st.rerun()
            else:
                st.error(f"❌ {message}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Retour espace étudiant ───────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("← Retour à l'espace étudiant", type="secondary", use_container_width=True):
        st.switch_page("pages/1_Accueil.py")

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;margin-top:1.5rem">
    <p style="color:#475569;font-size:0.7rem;border-top:1px solid rgba(255,255,255,0.06);
              padding-top:1rem">
        🎓 UniSchedule · © 2025 · Toutes les tentatives sont enregistrées
    </p>
</div>
""", unsafe_allow_html=True)
