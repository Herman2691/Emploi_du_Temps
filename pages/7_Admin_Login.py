# pages/7_Admin_Login.py
import streamlit as st
from utils.auth import login, is_authenticated, get_current_user
from utils.components import auth_page_css

# Redirection vers le login unifié
st.switch_page("pages/1_Accueil.py")

st.markdown(auth_page_css("#2563EB", "#1D4ED8"), unsafe_allow_html=True)

# CSS : colonne centrale stylée comme une carte
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

st.markdown("<div style='height:3vh'></div>", unsafe_allow_html=True)

_, col, _ = st.columns([1, 1.4, 1])

with col:

    # ── En-tête compact ────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;margin-bottom:1.8rem">
    <div style="width:64px;height:64px;
                background:linear-gradient(135deg,#2563EB,#1D4ED8);
                border-radius:18px;margin:0 auto 1rem;
                display:flex;align-items:center;justify-content:center;
                font-size:2rem;
                box-shadow:0 6px 22px rgba(37,99,235,0.28)">🔐</div>
    <h2 style="color:#1E293B;font-family:'Poppins',sans-serif;
               font-size:1.5rem;font-weight:700;margin:0;line-height:1.2">
        Espace Administrateur
    </h2>
    <p style="color:#64748B;font-size:0.8rem;margin:0.4rem 0 0">
        Accès restreint · Personnel autorisé uniquement
    </p>
</div>
""", unsafe_allow_html=True)

    # ── Champs de connexion ────────────────────────────────────────────────────
    email    = st.text_input("Adresse e-mail", placeholder="admin@universite.dz", key="adm_email")
    password = st.text_input("Mot de passe",   placeholder="••••••••",
                              type="password",  key="adm_password")

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

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

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    if st.button("← Retour à l'espace étudiant", type="secondary", use_container_width=True):
        st.switch_page("pages/1_Accueil.py")

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;margin-top:1.5rem">
    <p style="color:#94A3B8;font-size:0.68rem">
        🎓 UniSchedule · © 2025 · Toutes les tentatives sont enregistrées
    </p>
</div>
""", unsafe_allow_html=True)
