# pages/10_Student_Auth.py
import streamlit as st
from utils.auth import login_student, register_student, get_current_student
from utils.components import auth_page_css, auth_header
from db.queries import UniversityQueries, StudentRegistryQueries

# Redirection si déjà connecté
if get_current_student():
    st.switch_page("pages/11_Student_Dashboard.py")

st.markdown(auth_page_css("#059669", "#047857"), unsafe_allow_html=True)
st.markdown("""
<style>
.registry-card {
    background: #ECFDF5;
    border: 1px solid #6EE7B7;
    border-left: 3px solid #059669;
    border-radius: 10px; padding: 0.75rem 1rem; margin: 0.5rem 0 1rem;
}
.registry-card .rc-label {
    color: #059669; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; font-weight: 600;
}
.registry-card .rc-value { color: #065F46; font-size: 0.95rem; font-weight: 700; }
.registry-card .rc-sub   { color: #6B7280; font-size: 0.78rem; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
_, col, _ = st.columns([1, 1.6, 1])

with col:
    auth_header("🎓", "Espace Étudiant", "UniSchedule · Vos cours, TPs et notes", "#059669")

    tab_login, tab_register = st.tabs(["🔑 Se connecter", "📝 Créer un compte"])

    try:
        universities = UniversityQueries.get_all()
    except Exception as e:
        st.error(f"Erreur : {e}")
        universities = []

    # ── CONNEXION ─────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("""
<div style="background:white;border:1px solid #E2E8F0;
            border-radius:16px;padding:1.75rem 1.75rem 1.25rem;margin-top:0.5rem;
            box-shadow:0 4px 20px rgba(0,0,0,0.06),0 1px 3px rgba(0,0,0,0.04)">
""", unsafe_allow_html=True)

        uni_login = st.selectbox(
            "Université *",
            options=universities,
            format_func=lambda u: u["name"],
            index=None,
            placeholder="— Sélectionner votre université —",
            key="login_uni"
        )
        login_input = st.text_input(
            "Numéro étudiant ou nom d'utilisateur *",
            placeholder="ex: 2024001234 ou jean.dupont",
            key="login_input"
        )
        pwd_login = st.text_input(
            "Mot de passe *",
            type="password",
            placeholder="••••••••",
            key="login_pwd"
        )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("→ Se connecter", type="primary",
                     use_container_width=True, key="btn_login"):
            if not uni_login:
                st.error("Sélectionnez votre université.")
            elif not login_input or not pwd_login:
                st.error("Tous les champs sont obligatoires.")
            else:
                with st.spinner("Connexion..."):
                    ok, msg = login_student(login_input.strip(),
                                            uni_login["id"], pwd_login)
                if ok:
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── INSCRIPTION ───────────────────────────────────────────────────────────
    with tab_register:
        st.markdown("""
<div style="background:white;border:1px solid #E2E8F0;
            border-radius:16px;padding:1.75rem 1.75rem 1.25rem;margin-top:0.5rem;
            box-shadow:0 4px 20px rgba(0,0,0,0.06),0 1px 3px rgba(0,0,0,0.04)">
""", unsafe_allow_html=True)

        st.markdown("""
        <p style="color:#64748B;font-size:0.82rem;margin-bottom:1rem">
            Entrez votre numéro étudiant pour vérifier votre inscription,
            puis choisissez un nom d'utilisateur et un mot de passe.
        </p>
        """, unsafe_allow_html=True)

        uni_reg = st.selectbox(
            "Université *",
            options=universities,
            format_func=lambda u: u["name"],
            index=None,
            placeholder="— Sélectionner votre université —",
            key="reg_uni"
        )
        num_reg = st.text_input(
            "Numéro étudiant *",
            placeholder="ex: 2024001234",
            key="reg_num"
        )

        # Vérification live du numéro étudiant
        registry_entry = None
        if uni_reg and num_reg.strip():
            try:
                registry_entry = StudentRegistryQueries.verify(
                    num_reg.strip(), uni_reg["id"]
                )
                if registry_entry:
                    nom     = registry_entry.get("nom") or ""
                    postnom = registry_entry.get("postnom") or ""
                    prenom  = registry_entry.get("prenom") or ""
                    full    = " ".join(filter(None, [prenom, nom, postnom])) \
                              or registry_entry.get("full_name","")
                    _fi_d   = registry_entry.get("filiere_name") or registry_entry.get("promotion_txt") or ""
                    _opt_d  = registry_entry.get("option_name") or registry_entry.get("option_txt") or ""
                    _pr_d   = registry_entry.get("promotion_name") or ""
                    _yr_d   = registry_entry.get("annee_academique") or ""
                    _ec_d   = registry_entry.get("ecole_provenance") or ""
                    _dept_d = registry_entry.get("department_name") or ""

                    _sub_parts = []
                    if _fi_d:  _sub_parts.append(_fi_d)
                    if _opt_d: _sub_parts.append(_opt_d)
                    if _pr_d:  _sub_parts.append(_pr_d)
                    _sub1 = " · ".join(_sub_parts) if _sub_parts else ""

                    _sub2_parts = []
                    if _yr_d:   _sub2_parts.append(f"Année : {_yr_d}")
                    if _dept_d: _sub2_parts.append(f"Dép. : {_dept_d}")
                    if _ec_d:   _sub2_parts.append(f"École : {_ec_d}")
                    _sub2 = " · ".join(_sub2_parts)

                    st.markdown(f"""
<div class="registry-card">
    <div class="rc-label">✓ Étudiant trouvé dans la liste d'inscription</div>
    <div class="rc-value">{full}</div>
    {f'<div class="rc-sub">{_sub1}</div>' if _sub1 else ''}
    {f'<div class="rc-sub" style="margin-top:2px;font-size:0.74rem">{_sub2}</div>' if _sub2 else ''}
</div>
""", unsafe_allow_html=True)
                    if registry_entry.get("is_registered"):
                        st.warning("Un compte existe déjà pour ce numéro étudiant.")
                        registry_entry = None
                else:
                    if len(num_reg.strip()) >= 6:
                        st.error("Numéro étudiant non reconnu. Contactez l'administration.")
            except Exception:
                pass

        username_reg = st.text_input(
            "Nom d'utilisateur * (pour la connexion)",
            placeholder="ex: jean.dupont",
            key="reg_username"
        )

        col_pwd1, col_pwd2 = st.columns(2)
        with col_pwd1:
            pwd1_reg = st.text_input("Mot de passe *",
                                      type="password", key="reg_pwd1",
                                      placeholder="Min 8 caractères")
        with col_pwd2:
            pwd2_reg = st.text_input("Confirmer *",
                                      type="password", key="reg_pwd2",
                                      placeholder="••••••••")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        btn_disabled = (registry_entry is None)
        if st.button("📝 Créer mon compte", type="primary",
                     use_container_width=True, key="btn_register",
                     disabled=btn_disabled):
            if not uni_reg:
                st.error("Sélectionnez votre université.")
            else:
                with st.spinner("Création du compte..."):
                    ok, msg = register_student(
                        student_number=num_reg,
                        university_id=uni_reg["id"],
                        username=username_reg,
                        password=pwd1_reg,
                        confirm=pwd2_reg,
                    )
                if ok:
                    st.success(f"✅ {msg}")
                    st.info("Connectez-vous maintenant dans l'onglet 'Se connecter'.")
                else:
                    st.error(f"❌ {msg}")

        if btn_disabled and num_reg.strip():
            st.caption("Le bouton s'active une fois le numéro étudiant reconnu.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("← Retour à l'accueil", type="secondary",
                 use_container_width=True):
        st.switch_page("pages/1_Accueil.py")

    st.markdown("""
    <div style="text-align:center;margin-top:1.5rem">
        <p style="color:#334155;font-size:0.72rem">
            🎓 UniSchedule &nbsp;·&nbsp; © 2025
        </p>
    </div>
    """, unsafe_allow_html=True)
