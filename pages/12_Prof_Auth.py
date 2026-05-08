# pages/12_Prof_Auth.py
import streamlit as st
from utils.auth import login, get_current_user
from utils.components import auth_page_css, auth_header

# Redirection si déjà connecté en tant que professeur
user = get_current_user()
if user and user.get("role") == "professeur":
    st.switch_page("pages/9_Prof_Dashboard.py")

st.markdown(auth_page_css("#7C3AED", "#6D28D9"), unsafe_allow_html=True)

st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
_, col, _ = st.columns([1, 1.6, 1])

with col:
    auth_header("👨‍🏫", "Espace Professeur", "UniSchedule · Gérez vos cours et TPs", "#7C3AED")

    st.markdown("""
<div style="background:white;border:1px solid #E2E8F0;
            border-radius:18px;padding:2rem 2rem 1.5rem;
            box-shadow:0 4px 24px rgba(0,0,0,0.07),0 1px 4px rgba(0,0,0,0.04)">
""", unsafe_allow_html=True)

    email    = st.text_input("Adresse e-mail", placeholder="prof@universite.dz", key="prof_email")
    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
    password = st.text_input("Mot de passe", placeholder="••••••••",
                              type="password", key="prof_password")
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if st.button("→ Se connecter", type="primary", use_container_width=True):
        if not email or not password:
            st.error("Veuillez renseigner vos identifiants.")
        else:
            with st.spinner("Authentification..."):
                success, message = login(email.strip(), password)
            if success:
                current = get_current_user()
                if current and current.get("role") == "professeur":
                    st.rerun()
                else:
                    # Compte trouvé mais pas professeur
                    from utils.auth import logout
                    logout()
                    st.error("❌ Ce compte n'est pas un compte professeur.")
            else:
                st.error(f"❌ {message}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("← Retour à l'accueil", type="secondary", use_container_width=True):
        st.switch_page("pages/1_Accueil.py")

    st.markdown("""
<div style="text-align:center;margin-top:1.5rem">
    <p style="color:#1E293B;font-size:0.7rem">🎓 UniSchedule · © 2025</p>
</div>
""", unsafe_allow_html=True)
