# pages/7_Admin_Login.py
"""
Page de connexion administrateur — Interface autonome et sécurisée.
Accessible uniquement via URL directe : localhost:8501/Admin_Login
Complètement séparée de l'espace étudiant — aucun lien depuis la sidebar.
"""

import streamlit as st
from utils.auth import login, is_authenticated

# Redirection si déjà connecté
if is_authenticated():
    st.switch_page("pages/8_Admin_Dashboard.py")

# ── Design autonome : fond sombre, sidebar masquée ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500&display=swap');

    /* Masquer entièrement la sidebar sur cette page */
    [data-testid="stSidebar"]       { display: none !important; }
    [data-testid="collapsedControl"]{ display: none !important; }
    #MainMenu, footer, header       { visibility: hidden !important; }

    /* Fond sombre back-office */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #0F172A 100%) !important;
        min-height: 100vh;
        font-family: 'Inter', sans-serif;
    }

    /* Inputs dark */
    .stTextInput > div > div > input {
        background: #0F172A !important;
        border: 1px solid #334155 !important;
        color: #F1F5F9 !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.2) !important;
    }
    .stTextInput label {
        color: #94A3B8 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
    }

    /* Bouton principal */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.02em !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(37,99,235,0.4) !important;
    }

    /* Bouton secondaire */
    div[data-testid="stButton"] > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #334155 !important;
        color: #64748B !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        border-color: #475569 !important;
        color: #94A3B8 !important;
        background: rgba(255,255,255,0.03) !important;
    }

    /* Alertes dark */
    .stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ── Layout centré ──────────────────────────────────────────────────────────────
st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)

_, col, _ = st.columns([1, 1.6, 1])

with col:
    # ── En-tête ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:2.5rem">
        <div style="width:72px;height:72px;
                    background:linear-gradient(135deg,#2563EB 0%,#0EA5E9 100%);
                    border-radius:20px;margin:0 auto 1.25rem;
                    display:flex;align-items:center;justify-content:center;
                    font-size:2.2rem;
                    box-shadow:0 12px 32px rgba(37,99,235,0.45)">
            🔐
        </div>
        <h1 style="color:#F1F5F9;font-family:'Poppins',sans-serif;
                   font-size:1.9rem;font-weight:700;margin:0;line-height:1.2">
            Espace Administrateur
        </h1>
        <p style="color:#64748B;font-size:0.875rem;margin:0.5rem 0 0;line-height:1.5">
            Accès restreint · Personnel autorisé uniquement
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Carte formulaire ─────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#1E293B;border:1px solid #334155;border-radius:20px;
                padding:2rem 2rem 1.5rem;box-shadow:0 25px 60px rgba(0,0,0,0.5)">
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
                st.success(f"✅ {message}")
                st.switch_page("pages/8_Admin_Dashboard.py")
            else:
                st.error(f"❌ {message}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Retour espace étudiant ───────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("← Retour à l'espace étudiant", type="secondary", use_container_width=True):
        st.switch_page("pages/1_Accueil.py")

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-top:2rem">
        <p style="color:#1E293B;font-size:0.72rem;margin:0;
                  border-top:1px solid #1E293B;padding-top:1rem;color:#334155">
            🎓 UniSchedule &nbsp;·&nbsp; © 2025 &nbsp;·&nbsp;
            Toutes les tentatives de connexion sont enregistrées
        </p>
    </div>
    """, unsafe_allow_html=True)
