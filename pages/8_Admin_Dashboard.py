# pages/8_Admin_Dashboard.py
import streamlit as st
from utils.auth import require_auth, get_current_user, ROLE_LABELS, create_admin
from utils.components import inject_global_css, page_header, role_badge, announcement_card, render_schedule_table

inject_global_css()
require_auth()

user = get_current_user()
role = user["role"]

# ── En-tête (masqué pour admin_universite qui gère le sien) ──────────────────
if role != "admin_universite":
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        page_header("Tableau de Bord", f"Bienvenue, {user['name']}", "📊")
    with col_h2:
        role_badge(role)
        st.caption(ROLE_LABELS.get(role, role))
    st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SUPER ADMIN
# ══════════════════════════════════════════════════════════════════════════════
def render_super_admin():
    from db.queries import UniversityQueries, UserQueries
    from utils.auth import hash_password

    tab_unis, tab_admins, tab_analytics = st.tabs(["🏛️ Universités", "👥 Comptes Administrateurs", "📊 Analytiques"])

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 : UNIVERSITÉS — Ajouter / Modifier / Désactiver / Réactiver
    # ══════════════════════════════════════════════════════════════════════════
    with tab_unis:
        try:
            unis = UniversityQueries.get_all(active_only=False)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        active_unis   = [u for u in unis if u.get("is_active")]
        inactive_unis = [u for u in unis if not u.get("is_active")]

        c1, c2, c3 = st.columns(3)
        c1.metric("Universités actives",   len(active_unis))
        c2.metric("Universités désactivées", len(inactive_unis))
        c3.metric("Total",                 len(unis))
        st.divider()

        # ── Ajouter ──────────────────────────────────────────────────────────
        with st.expander("➕ Ajouter une université"):
            with st.form("add_uni"):
                name    = st.text_input("Nom *")
                address = st.text_area("Adresse")
                logo_up = st.file_uploader("Logo de l'université", type=["png","jpg","jpeg","webp","svg"], key="add_uni_logo")
                website = st.text_input("Site web (optionnel)")
                color   = st.color_picker("Couleur principale", value="#2563EB")
                if st.form_submit_button("Créer", type="primary"):
                    if not name.strip():
                        st.error("Le nom est obligatoire.")
                    else:
                        try:
                            photo_url = None
                            if logo_up:
                                from utils.storage import upload_file as _upload
                                _stored, _ = _upload(logo_up.read(), logo_up.name, "university-logos")
                                photo_url = _stored
                            UniversityQueries.create(name.strip(), address, photo_url, website, color)
                            st.success(f"✅ Université '{name.strip()}' créée !"); st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

        # ── Universités actives ───────────────────────────────────────────────
        if active_unis:
            st.markdown("#### ✅ Universités actives")
            for uni in active_unis:
                with st.expander(f"🏛️ {uni['name']}"):
                    # Logo display (outside form)
                    from utils.components import get_logo_display_url as _gldurl
                    _lurl = _gldurl(uni.get("photo_url",""))
                    if _lurl:
                        st.image(_lurl, width=80)

                    # Stats
                    try:
                        stats = UniversityQueries.get_stats(uni["id"])
                        if stats:
                            s1, s2, s3 = st.columns(3)
                            s1.metric("Facultés",     stats.get("faculties_count", 0))
                            s2.metric("Départements", stats.get("departments_count", 0))
                            s3.metric("Promotions",   stats.get("promotions_count", 0))
                    except Exception:
                        pass

                    st.divider()

                    # Current logo preview (outside form)
                    _cur_logo = _gldurl(uni.get("photo_url",""))
                    if _cur_logo:
                        st.image(_cur_logo, width=60, caption="Logo actuel")

                    # Modifier
                    st.markdown("**✏️ Modifier**")
                    with st.form(f"edit_uni_{uni['id']}"):
                        nn = st.text_input("Nom *",      value=uni["name"])
                        na = st.text_input("Adresse",    value=uni.get("address", ""))
                        np_file = st.file_uploader("Nouveau logo", type=["png","jpg","jpeg","webp","svg"], key=f"logo_up_{uni['id']}")
                        nw = st.text_input("Site web",   value=uni.get("website", ""))
                        nc = st.color_picker(
                            "Couleur principale",
                            value=uni.get("primary_color") or "#2563EB"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Sauvegarder", type="primary"):
                                if not nn.strip():
                                    st.error("Le nom est obligatoire.")
                                else:
                                    try:
                                        _new_photo = uni.get("photo_url") or None
                                        if np_file:
                                            from utils.storage import upload_file as _upload
                                            _stored, _ = _upload(np_file.read(), np_file.name, "university-logos")
                                            _new_photo = _stored
                                        UniversityQueries.update(uni["id"], nn, na, _new_photo, nw, nc)
                                        st.success("✅ Université mise à jour !"); st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                        with col2:
                            if st.form_submit_button("⛔ Désactiver"):
                                UniversityQueries.delete(uni["id"])
                                st.warning(f"'{uni['name']}' désactivée."); st.rerun()

        # ── Universités désactivées ───────────────────────────────────────────
        if inactive_unis:
            st.markdown("#### ⛔ Universités désactivées")
            for uni in inactive_unis:
                with st.expander(f"🔒 {uni['name']} (désactivée)"):
                    st.caption(f"📍 {uni.get('address','—')}")
                    if st.button("♻️ Réactiver", key=f"reactivate_uni_{uni['id']}", type="primary"):
                        try:
                            from db.connection import execute_query
                            execute_query("UPDATE universities SET is_active=TRUE WHERE id=%s",
                                          (uni["id"],), fetch="none")
                            st.success(f"✅ '{uni['name']}' réactivée !"); st.rerun()
                        except Exception as e:
                            st.error(str(e))
                    if st.button("🗑️ Supprimer définitivement", key=f"delete_uni_{uni['id']}"):
                        try:
                            from db.connection import execute_query
                            execute_query("DELETE FROM universities WHERE id=%s",
                                          (uni["id"],), fetch="none")
                            st.success("Supprimée."); st.rerun()
                        except Exception as e:
                            st.error(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 : COMPTES ADMINISTRATEURS — Créer / Modifier / Désactiver
    # ══════════════════════════════════════════════════════════════════════════
    with tab_admins:
        try:
            unis  = UniversityQueries.get_all()
            # Récupère tous les admins (tous rôles sauf super_admin)
            from db.connection import execute_query
            admins = execute_query("""
                SELECT u.*, univ.name AS university_name
                FROM users u
                LEFT JOIN universities univ ON u.university_id = univ.id
                WHERE u.role != 'super_admin'
                ORDER BY u.role, u.name
            """) or []
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        # ── Flash message après création ─────────────────────────────────────
        if "_admin_flash" in st.session_state:
            _lvl, _fmsg = st.session_state.pop("_admin_flash")
            getattr(st, _lvl)(_fmsg)

        # ── Créer un nouvel admin ─────────────────────────────────────────────
        with st.expander("➕ Créer un compte administrateur"):
            with st.form("create_admin_uni"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name  = st.text_input("Nom complet *")
                    new_email = st.text_input("Email *")
                    new_pwd   = st.text_input("Mot de passe * (min 8 car.)", type="password")
                with col2:
                    new_role = st.selectbox("Rôle *", [
                        "admin_universite",
                        "admin_faculte",
                        "admin_departement",
                    ], format_func=lambda r: ROLE_LABELS.get(r, r))
                    uni_c = st.selectbox("Université *", options=unis or [],
                                         format_func=lambda u: u["name"]) if unis else None

                if st.form_submit_button("Créer le compte", type="primary"):
                    if uni_c:
                        ok, msg = create_admin(
                            name=new_name, email=new_email, password=new_pwd,
                            role=new_role, university_id=uni_c["id"]
                        )
                        if ok:
                            st.session_state["_admin_flash"] = (
                                "success",
                                f"✅ Administrateur '{new_name}' créé avec succès !"
                            )
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("Créez d'abord une université.")

        st.divider()

        # ── Liste des admins existants ────────────────────────────────────────
        if not admins:
            st.info("Aucun administrateur créé pour l'instant.")
        else:
            active_admins   = [a for a in admins if a.get("is_active")]
            inactive_admins = [a for a in admins if not a.get("is_active")]

            a1, a2 = st.columns(2)
            a1.metric("Comptes actifs",    len(active_admins))
            a2.metric("Comptes désactivés", len(inactive_admins))
            st.divider()

            if active_admins:
                st.markdown("#### ✅ Comptes actifs")
                for adm in active_admins:
                    role_icon = {"admin_universite":"🔵","admin_faculte":"🟢","admin_departement":"🟡"}.get(adm["role"],"⚪")
                    uni_label = adm.get("university_name") or "—"
                    with st.expander(f"{role_icon} {adm['name']} — {ROLE_LABELS.get(adm['role'], adm['role'])} · {uni_label}"):

                        col_edit, col_pwd, col_action = st.columns([3, 2, 1])

                        # Modifier infos
                        with col_edit:
                            st.markdown("**✏️ Modifier les infos**")
                            with st.form(f"edit_adm_{adm['id']}"):
                                en = st.text_input("Nom",   value=adm["name"])
                                ee = st.text_input("Email", value=adm["email"])
                                er = st.selectbox("Rôle", [
                                    "admin_universite","admin_faculte","admin_departement"
                                ], index=["admin_universite","admin_faculte","admin_departement"].index(adm["role"])
                                   if adm["role"] in ["admin_universite","admin_faculte","admin_departement"] else 0,
                                   format_func=lambda r: ROLE_LABELS.get(r, r))
                                eu = st.selectbox("Université", options=unis or [],
                                                  format_func=lambda u: u["name"],
                                                  index=next((i for i,u in enumerate(unis or []) if u["id"]==adm.get("university_id")),0))
                                if st.form_submit_button("💾 Sauvegarder", type="primary"):
                                    try:
                                        execute_query(
                                            "UPDATE users SET name=%s, email=%s, role=%s, university_id=%s WHERE id=%s",
                                            (en.strip(), ee.strip().lower(), er,
                                             eu["id"] if eu else None, adm["id"]), fetch="none"
                                        )
                                        st.success("✅ Compte mis à jour !"); st.rerun()
                                    except Exception as e:
                                        st.error(str(e))

                        # Réinitialiser mot de passe
                        with col_pwd:
                            st.markdown("**🔑 Nouveau mot de passe**")
                            with st.form(f"pwd_adm_{adm['id']}"):
                                new_p  = st.text_input("Nouveau MDP *", type="password")
                                new_p2 = st.text_input("Confirmer *",   type="password")
                                if st.form_submit_button("Réinitialiser"):
                                    if not new_p or len(new_p) < 8:
                                        st.error("Min 8 caractères.")
                                    elif new_p != new_p2:
                                        st.error("Les mots de passe ne correspondent pas.")
                                    else:
                                        try:
                                            UserQueries.update_password(adm["id"], hash_password(new_p))
                                            st.success("✅ Mot de passe mis à jour !")
                                        except Exception as e:
                                            st.error(str(e))

                        # Désactiver
                        with col_action:
                            st.markdown("**⛔ Actions**")
                            if st.button("⛔ Désactiver", key=f"deact_adm_{adm['id']}"):
                                UserQueries.deactivate(adm["id"])
                                st.warning(f"Compte de '{adm['name']}' désactivé."); st.rerun()

            if inactive_admins:
                st.markdown("#### 🔒 Comptes désactivés")
                for adm in inactive_admins:
                    with st.expander(f"🔒 {adm['name']} ({adm['email']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("♻️ Réactiver", key=f"react_adm_{adm['id']}", type="primary"):
                                try:
                                    execute_query("UPDATE users SET is_active=TRUE WHERE id=%s",
                                                  (adm["id"],), fetch="none")
                                    st.success("✅ Compte réactivé !"); st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                        with col2:
                            if st.button("🗑️ Supprimer définitivement", key=f"del_adm_{adm['id']}"):
                                try:
                                    execute_query("DELETE FROM users WHERE id=%s",
                                                  (adm["id"],), fetch="none")
                                    st.success("Supprimé."); st.rerun()
                                except Exception as e:
                                    st.error(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 : ANALYTIQUES
    # ══════════════════════════════════════════════════════════════════════════
    with tab_analytics:
        import pandas as pd
        from db.queries import AnalyticsQueries

        try:
            summary   = AnalyticsQueries.get_global_summary() or {}
            unis_data = AnalyticsQueries.get_universities_summary() or []
            reg_data  = AnalyticsQueries.get_recent_student_registrations(30) or []
        except Exception as e:
            st.error(f"Erreur chargement analytiques : {e}"); return

        # ── Métriques globales ───────────────────────────────────────────────
        st.markdown("#### Vue d'ensemble de la plateforme")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Universités",   summary.get("uni_count", 0))
        m2.metric("Étudiants",     summary.get("student_count", 0))
        m3.metric("Professeurs",   summary.get("prof_count", 0))
        m4.metric("TPs créés",     summary.get("tp_count", 0))
        m5.metric("Soumissions",   summary.get("submission_count", 0))
        m6.metric("Notes publiées",summary.get("grade_count", 0))

        st.divider()

        if unis_data:
            col_bar1, col_bar2 = st.columns(2)

            # Étudiants par université
            with col_bar1:
                st.markdown("##### Étudiants par université")
                df_stu = pd.DataFrame(unis_data)[["name","students"]].rename(
                    columns={"name": "Université", "students": "Étudiants"})
                st.bar_chart(df_stu.set_index("Université"))

            # Créneaux par université
            with col_bar2:
                st.markdown("##### Créneaux par université")
                df_sch = pd.DataFrame(unis_data)[["name","schedules"]].rename(
                    columns={"name": "Université", "schedules": "Créneaux"})
                st.bar_chart(df_sch.set_index("Université"))

            st.divider()
            st.markdown("##### Tableau détaillé")
            df_full = pd.DataFrame(unis_data)[["name","students","professors","schedules"]].rename(
                columns={"name":"Université","students":"Étudiants",
                         "professors":"Professeurs","schedules":"Créneaux"})
            st.dataframe(df_full, use_container_width=True, hide_index=True)

        if reg_data:
            st.divider()
            st.markdown("##### Nouvelles inscriptions étudiantes (30 derniers jours)")
            df_reg = pd.DataFrame(reg_data).rename(
                columns={"date": "Date", "count": "Inscriptions"})
            df_reg["Date"] = pd.to_datetime(df_reg["Date"])
            st.line_chart(df_reg.set_index("Date"))
        else:
            st.info("Aucune inscription dans les 30 derniers jours.")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN UNIVERSITÉ
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_universite():
    from db.queries import (FacultyQueries, UniversityQueries, DepartmentQueries,
                             PromotionQueries, StudentQueries, ProfessorQueries,
                             AnnouncementQueries)
    from db.connection import execute_query  # noqa: F811

    uni_id = user["university_id"]
    if not uni_id:
        st.error("Aucune université associée à ce compte."); return

    try:
        uni      = UniversityQueries.get_by_id(uni_id)
        faculties = FacultyQueries.get_by_university(uni_id)
        stats    = UniversityQueries.get_stats(uni_id) or {}
    except Exception as e:
        st.error(f"Erreur : {e}"); return

    uni_name = uni["name"] if uni else "Votre université"

    # ── En-tête université ────────────────────────────────────────────────────
    primary = uni.get("primary_color") or "#2563EB"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{primary}dd,{primary}99);
                border-radius:14px;padding:1.5rem 2rem;color:white;margin-bottom:1.5rem">
        <h2 style="margin:0;font-family:'Poppins',sans-serif;font-size:1.5rem">
            🏛️ {uni_name}
        </h2>
        <p style="margin:0.3rem 0 0;opacity:0.85;font-size:0.85rem">
            Tableau de bord · Admin Université · {user['name']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats rapides ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Facultés",     stats.get("faculties_count", len(faculties)))
    c2.metric("Départements", stats.get("departments_count", 0))
    c3.metric("Promotions",   stats.get("promotions_count", 0))
    c4.metric("Étudiants",    stats.get("students_count", 0))
    st.divider()

    tab_fac, tab_dept, tab_profs, tab_admins, tab_announce = st.tabs([
        "📚 Facultés",
        "🏬 Départements",
        "👨‍🏫 Professeurs",
        "👥 Administrateurs",
        "📢 Communiqués",
    ])

    # ── ONGLET 1 : FACULTÉS ───────────────────────────────────────────────────
    with tab_fac:
        with st.expander("➕ Ajouter une faculté"):
            with st.form("add_fac"):
                name = st.text_input("Nom *")
                desc = st.text_area("Description")
                if st.form_submit_button("Créer", type="primary"):
                    if not name.strip():
                        st.error("Nom obligatoire.")
                    else:
                        try:
                            FacultyQueries.create(name.strip(), uni_id, desc)
                            st.success("✅ Faculté créée !"); st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

        if not faculties:
            st.info("Aucune faculté créée pour l'instant.")
        for fac in faculties:
            # Compter les départements de cette faculté
            try:
                depts = DepartmentQueries.get_by_faculty(fac["id"])
            except Exception:
                depts = []
            with st.expander(f"📗 {fac['name']} — {len(depts)} département(s)"):
                with st.form(f"edit_fac_{fac['id']}"):
                    nn = st.text_input("Nom",        value=fac["name"])
                    nd = st.text_area("Description", value=fac.get("description",""))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                FacultyQueries.update(fac["id"], nn, nd)
                                st.success("✅ Faculté mise à jour !"); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                FacultyQueries.delete(fac["id"])
                                st.success("✅ Faculté supprimée."); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ── ONGLET 2 : DÉPARTEMENTS ───────────────────────────────────────────────
    with tab_dept:
        if not faculties:
            st.info("Créez d'abord des facultés.")
        else:
            with st.expander("➕ Ajouter un département"):
                with st.form("add_dept_uni"):
                    fac_sel = st.selectbox("Faculté *", options=faculties,
                                           format_func=lambda f: f["name"])
                    dept_name = st.text_input("Nom du département *")
                    dept_desc = st.text_area("Description")
                    if st.form_submit_button("Créer", type="primary"):
                        if not dept_name.strip():
                            st.error("Nom obligatoire.")
                        else:
                            try:
                                DepartmentQueries.create(dept_name.strip(),
                                                         fac_sel["id"], dept_desc)
                                st.success("✅ Département créé !"); st.rerun()
                            except Exception as e:
                                st.error(str(e))

            for fac in faculties:
                try:
                    depts = DepartmentQueries.get_by_faculty(fac["id"])
                except Exception:
                    depts = []
                if depts:
                    st.markdown(f"**📗 {fac['name']}**")
                    for dept in depts:
                        with st.expander(f"🏬 {dept['name']}"):
                            with st.form(f"edit_dept_{dept['id']}"):
                                dn = st.text_input("Nom", value=dept["name"])
                                dd = st.text_area("Description",
                                                  value=dept.get("description",""))
                                c1d, c2d = st.columns(2)
                                with c1d:
                                    if st.form_submit_button("💾 Sauvegarder"):
                                        try:
                                            DepartmentQueries.update(dept["id"], dn, dd)
                                            st.success("✅ Département mis à jour !"); st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur : {e}")
                                with c2d:
                                    if st.form_submit_button("🗑️ Supprimer"):
                                        try:
                                            DepartmentQueries.delete(dept["id"])
                                            st.success("✅ Département supprimé."); st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur : {e}")

    # ── ONGLET 3 : PROFESSEURS ────────────────────────────────────────────────
    with tab_profs:
        try:
            all_profs = ProfessorQueries.get_by_university(uni_id)
        except Exception as e:
            st.error(str(e)); all_profs = []

        actifs   = [p for p in all_profs if p.get("is_active")]
        inactifs = [p for p in all_profs if not p.get("is_active")]

        c1, c2 = st.columns(2)
        c1.metric("Actifs",   len(actifs))
        c2.metric("Inactifs", len(inactifs))
        st.divider()

        # ── Recherche ──────────────────────────────────────────────────────
        search = st.text_input("🔍 Rechercher un professeur", placeholder="Nom...")
        profs_filtered = [p for p in all_profs
                          if not search or search.lower() in p["name"].lower()]

        for prof in profs_filtered:
            is_active   = prof.get("is_active", True)
            statut_icon = "🟢" if prof.get("statut") == "Contractuel" else "🔵"
            state_icon  = "✅" if is_active else "⛔"
            with st.expander(
                f"{state_icon} {prof['name']} · {statut_icon} {prof.get('statut','—')} "
                f"— {prof.get('department_name','—')} / {prof.get('faculty_name','—')}"
            ):
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.caption(f"📧 {prof.get('email','—')} · 📞 {prof.get('phone','—')}")
                with col_btn:
                    if is_active:
                        if st.button("⛔ Désactiver",
                                     key=f"uni_deact_prof_{prof['id']}",
                                     use_container_width=True):
                            ProfessorQueries.set_active(prof["id"], False)
                            st.warning(f"⛔ {prof['name']} désactivé."); st.rerun()
                    else:
                        if st.button("✅ Activer",
                                     key=f"uni_act_prof_{prof['id']}",
                                     type="primary",
                                     use_container_width=True):
                            ProfessorQueries.set_active(prof["id"], True)
                            st.success(f"✅ {prof['name']} activé."); st.rerun()

    # ── ONGLET 4 : ADMINISTRATEURS ────────────────────────────────────────────
    with tab_admins:
        try:
            admins_uni = execute_query("""
                SELECT u.*, f.name AS faculty_name
                FROM users u
                LEFT JOIN faculties f ON u.faculty_id = f.id
                WHERE u.university_id = %s AND u.role != 'super_admin'
                ORDER BY u.role, u.name
            """, (uni_id,)) or []
        except Exception as e:
            st.error(str(e)); admins_uni = []

        st.markdown(f"**{len(admins_uni)} compte(s) administrateur(s)**")
        for adm in admins_uni:
            role_icon = {"admin_faculte": "🟢", "admin_departement": "🟡",
                         "professeur": "🟣"}.get(adm["role"], "⚪")
            st.markdown(
                f"{role_icon} **{adm['name']}** — {adm['email']}  \n"
                f"<span style='color:#94A3B8;font-size:0.78rem'>"
                f"{ROLE_LABELS.get(adm['role'], adm['role'])}"
                + (f" · {adm['faculty_name']}" if adm.get('faculty_name') else "")
                + "</span>",
                unsafe_allow_html=True
            )
        st.divider()

        st.markdown("#### ➕ Créer un admin faculté")
        if not faculties:
            st.info("Créez d'abord des facultés.")
        else:
            with st.form("create_admin_fac"):
                name     = st.text_input("Nom complet *")
                email    = st.text_input("Email *")
                password = st.text_input("Mot de passe *", type="password")
                fac_c    = st.selectbox("Faculté *", options=faculties,
                                        format_func=lambda f: f["name"])
                if st.form_submit_button("Créer", type="primary"):
                    ok, msg = create_admin(name=name, email=email, password=password,
                                           role="admin_faculte",
                                           university_id=uni_id,
                                           faculty_id=fac_c["id"])
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ── ONGLET 4 : COMMUNIQUÉS ────────────────────────────────────────────────
    with tab_announce:
        from db.queries import AnnouncementQueries as _AQ
        try:
            announcements = _AQ.get_by_university(uni_id)
        except Exception:
            announcements = []

        st.metric("Communiqués actifs", len(announcements))
        st.divider()

        with st.expander("➕ Nouveau communiqué"):
            with st.form("add_ann_uni"):
                ann_title   = st.text_input("Titre *")
                ann_content = st.text_area("Contenu *")
                ann_pinned  = st.checkbox("📌 Épingler en haut")
                ann_expires = st.date_input("Date d'expiration (optionnel)", value=None)
                ann_file    = st.file_uploader(
                    "Fichier joint — PDF ou image (optionnel)",
                    type=["pdf", "jpg", "jpeg", "png", "gif", "webp"],
                    key="ann_file_uni"
                )
                if st.form_submit_button("Publier", type="primary"):
                    if not ann_title.strip() or not ann_content.strip():
                        st.error("Titre et contenu obligatoires.")
                    else:
                        from datetime import datetime as _dt
                        expires_dt = None
                        if ann_expires:
                            expires_dt = _dt.combine(ann_expires, _dt.max.time())
                        file_url = file_name = None
                        if ann_file:
                            try:
                                from utils.storage import upload_file, ANNOUNCEMENTS_BUCKET
                                file_url, _ = upload_file(
                                    ann_file.read(), ann_file.name,
                                    ANNOUNCEMENTS_BUCKET,
                                    folder=f"uni_{uni_id}"
                                )
                                file_name = ann_file.name
                            except Exception as _e:
                                st.warning(f"Fichier non uploadé : {_e}")
                        try:
                            _AQ.create(
                                title=ann_title.strip(),
                                content=ann_content.strip(),
                                university_id=uni_id,
                                created_by=user["id"],
                                is_pinned=ann_pinned,
                                expires_at=expires_dt,
                                file_url=file_url,
                                file_name=file_name,
                            )
                            st.success("✅ Communiqué publié !"); st.rerun()
                        except Exception as e:
                            st.error(str(e))

        if not announcements:
            st.info("Aucun communiqué publié.")
        else:
            for ann in announcements:
                with st.expander(f"{'📌 ' if ann.get('is_pinned') else ''}📢 {ann['title']}"):
                    announcement_card(ann)
                    if st.button("🗑️ Supprimer", key=f"del_ann_uni_{ann['id']}"):
                        _AQ.delete(ann["id"])
                        st.success("✅ Communiqué supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN FACULTÉ
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_faculte():
    from db.queries import DepartmentQueries, FacultyQueries

    fac_id = user["faculty_id"]
    uni_id = user["university_id"]
    if not fac_id:
        st.error("Aucune faculté associée à ce compte."); return

    try:
        fac = FacultyQueries.get_by_id(fac_id)
    except Exception as e:
        st.error(f"Erreur : {e}"); return

    st.subheader(f"📚 {fac['name'] if fac else 'Votre faculté'}")
    tab_dept, tab_admins = st.tabs(["🏢 Départements", "👥 Admins Département"])

    with tab_dept:
        try:
            departments = DepartmentQueries.get_by_faculty(fac_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        st.metric("Départements", len(departments))
        st.divider()

        with st.expander("➕ Ajouter un département"):
            with st.form("add_dept"):
                name = st.text_input("Nom *")
                desc = st.text_area("Description")
                if st.form_submit_button("Créer", type="primary"):
                    if not name.strip():
                        st.error("Nom obligatoire.")
                    else:
                        DepartmentQueries.create(name.strip(), fac_id, desc)
                        st.success("✅ Département créé !"); st.rerun()

        for dept in departments:
            with st.expander(f"🏢 {dept['name']}"):
                with st.form(f"edit_dept_{dept['id']}"):
                    nn = st.text_input("Nom",        value=dept["name"])
                    nd = st.text_area("Description", value=dept.get("description",""))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                DepartmentQueries.update(dept["id"],nn,nd)
                                st.success("✅ Département mis à jour !"); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                DepartmentQueries.delete(dept["id"])
                                st.success("✅ Département supprimé."); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    with tab_admins:
        try:
            departments = DepartmentQueries.get_by_faculty(fac_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        if not departments:
            st.info("Créez d'abord des départements.")
        else:
            with st.form("create_admin_dept"):
                name     = st.text_input("Nom complet *")
                email    = st.text_input("Email *")
                password = st.text_input("Mot de passe *", type="password")
                dept_c   = st.selectbox("Département *", options=departments,
                                        format_func=lambda d: d["name"])
                if st.form_submit_button("Créer l'admin", type="primary"):
                    ok, msg = create_admin(name=name, email=email, password=password,
                                           role="admin_departement",
                                           university_id=uni_id,
                                           faculty_id=fac_id,
                                           department_id=dept_c["id"])
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DÉPARTEMENT
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_departement():
    from db.queries import (PromotionQueries, ClassQueries, CourseQueries,
                             ProfessorQueries, ScheduleQueries,
                             AnnouncementQueries, DepartmentQueries,
                             FiliereQueries, OptionEtudeQueries,
                             AcademicEnrollmentQueries,
                             GradeModificationRequestQueries,
                             AttendanceQueries, GradeClaimQueries)

    dept_id = user["department_id"]
    if not dept_id:
        st.error("Aucun département associé à ce compte."); return

    try:
        dept = DepartmentQueries.get_by_id(dept_id)
    except Exception as e:
        st.error(f"Erreur : {e}"); return

    _dept_uni_id = (dept.get("university_id") if dept else None) or user.get("university_id")
    _current_ay  = None
    if _dept_uni_id:
        try:
            from db.queries import AcademicYearQueries as _AYQ_hdr
            _current_ay = _AYQ_hdr.get_current(_dept_uni_id)
        except Exception:
            pass
    _ay_badge = (
        f"  ·  📅 {_current_ay['label']}"
        if _current_ay else ""
    )
    st.subheader(f"🏢 {dept['name'] if dept else 'Votre département'}{_ay_badge}")

    tabs = st.tabs(["🎓 Promotions", "🏫 Salles", "📘 Cours",
                    "👨‍🏫 Professeurs", "👨‍💼 Comptes Prof",
                    "📅 Emploi du Temps", "📢 Communiqués",
                    "👨‍🎓 Registre Étudiants", "🔐 Comptes Étudiants",
                    "📊 Résultats",
                    "🔬 Filières", "🗂️ Options", "📚 Inscriptions",
                    "✏️ Demandes de modification",
                    "📍 Présences", "📩 Réclamations",
                    "📋 Bulletins", "🗓️ Années acad.", "📈 Analyses"])

    # ── PROMOTIONS ────────────────────────────────────────────────────────────
    with tabs[0]:
        try:
            promotions = PromotionQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        st.metric("Promotions", len(promotions))
        st.divider()

        with st.expander("➕ Ajouter une promotion"):
            with st.form("add_promo"):
                name = st.text_input("Nom (ex: L1 Informatique) *")
                _default_ay = _current_ay["label"] if _current_ay else "2024-2025"
                year = st.text_input("Année académique *", value=_default_ay)
                if st.form_submit_button("Créer", type="primary"):
                    if name.strip() and year.strip():
                        PromotionQueries.create(name.strip(), year.strip(), dept_id)
                        st.success("✅ Promotion créée !"); st.rerun()
                    else:
                        st.error("Tous les champs sont obligatoires.")

        for promo in promotions:
            with st.expander(f"🎓 {promo['name']} ({promo['academic_year']})"):
                with st.form(f"edit_promo_{promo['id']}"):
                    nn = st.text_input("Nom",   value=promo["name"])
                    ny = st.text_input("Année", value=promo["academic_year"])
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                PromotionQueries.update(promo["id"],nn,ny)
                                st.success("✅ Promotion mise à jour !"); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                PromotionQueries.delete(promo["id"])
                                st.success("✅ Promotion supprimée."); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ── CLASSES ───────────────────────────────────────────────────────────────
    with tabs[1]:
        try:
            promotions = PromotionQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        if not promotions:
            st.info("Créez d'abord des promotions.")
        else:
            promo_sel = st.selectbox("Promotion", options=promotions,
                                     format_func=lambda p: f"{p['name']} ({p['academic_year']})",
                                     key="cls_promo")
            if promo_sel:
                try:
                    classes = ClassQueries.get_by_promotion(promo_sel["id"])
                except Exception as e:
                    st.error(f"Erreur : {e}"); return

                st.metric("Salles", len(classes))
                st.divider()

                with st.expander("➕ Ajouter une salle"):
                    with st.form("add_class"):
                        name     = st.text_input("Nom (ex: L1 A) *")
                        capacity = st.number_input("Capacité", min_value=1, max_value=200, value=30)
                        if st.form_submit_button("Créer", type="primary"):
                            if name.strip():
                                ClassQueries.create(name.strip(), promo_sel["id"], int(capacity))
                                st.success("✅ Salle créée !"); st.rerun()
                            else:
                                st.error("Nom obligatoire.")

                for cls in classes:
                    with st.expander(f"🏫 {cls['name']}"):
                        with st.form(f"edit_cls_{cls['id']}"):
                            nn = st.text_input("Nom",      value=cls["name"])
                            nc = st.number_input("Capacité", value=cls.get("capacity",30),
                                                 min_value=1, max_value=200)
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Sauvegarder"):
                                    try:
                                        ClassQueries.update(cls["id"],nn,int(nc))
                                        st.success("✅ Salle mise à jour !"); st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur : {e}")
                            with col2:
                                if st.form_submit_button("🗑️ Supprimer"):
                                    try:
                                        ClassQueries.delete(cls["id"])
                                        st.success("✅ Salle supprimée."); st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur : {e}")

    # ── COURS ─────────────────────────────────────────────────────────────────
    with tabs[2]:
        from db.queries import UEQueries as _UQT
        try:
            courses   = CourseQueries.get_by_department(dept_id)
            _ues_list = _UQT.get_by_department(dept_id) or []
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        total_h = sum(c.get("hours", 0) for c in courses)
        _cm1, _cm2, _cm3 = st.columns(3)
        _cm1.metric("Cours (EC)", len(courses))
        _cm2.metric("UEs définies", len(_ues_list))
        _cm3.metric("Volume horaire", f"{total_h}h")
        st.divider()

        with st.expander("➕ Ajouter un cours (EC)"):
            with st.form("add_course"):
                name   = st.text_input("Intitulé *")
                code   = st.text_input("Code (ex: INF301)")
                _hcol, _wcol = st.columns(2)
                hours  = _hcol.number_input("Heures", min_value=0, max_value=500, value=30)
                weight = _wcol.number_input("Coefficient", min_value=0.5, max_value=10.0,
                                            value=1.0, step=0.5)
                _ue_opts_add = [None] + _ues_list
                _ucol_add, _ccol_add = st.columns([3, 1])
                _sel_ue_add = _ucol_add.selectbox(
                    "Unité d'Enseignement (UE)",
                    _ue_opts_add,
                    format_func=lambda u: (
                        "— Sans UE —" if u is None
                        else f"[{u.get('group_label','?')}] {u.get('code','')} {u['name']}"
                    ),
                    key="ue_sel_add",
                )
                _cred_ec_add = _ccol_add.number_input(
                    "Crédits EC", value=1.0, min_value=0.5, step=0.5, key="cred_ec_add"
                )
                if st.form_submit_button("Créer", type="primary"):
                    if name.strip():
                        try:
                            new_course = CourseQueries.create(
                                name.strip(), code.strip(),
                                int(hours), float(weight), dept_id
                            )
                            if _sel_ue_add and new_course and new_course.get("id"):
                                _UQT.assign_course(new_course["id"],
                                                   _sel_ue_add["id"],
                                                   float(_cred_ec_add))
                            st.success("✅ Cours créé !"); st.rerun()
                        except Exception as _ce:
                            st.error(f"Erreur : {_ce}")
                    else:
                        st.error("Intitulé obligatoire.")

        for course in courses:
            _ue_tag = (f" — {course.get('ue_code','')} {course.get('ue_name','')}"
                       if course.get("ue_name") else "")
            with st.expander(
                f"📘 {course['name']} ({course.get('code','—')}){_ue_tag}"
            ):
                with st.form(f"edit_course_{course['id']}"):
                    nn = st.text_input("Intitulé",    value=course["name"])
                    nc = st.text_input("Code",         value=course.get("code",""))
                    _hcol, _wcol = st.columns(2)
                    nh = _hcol.number_input("Heures",  value=course.get("hours",0), min_value=0)
                    nw = _wcol.number_input("Coefficient",
                                            value=float(course.get("weight",1.0)),
                                            min_value=0.5, step=0.5)
                    # ── Affectation UE ──────────────────────────────────────
                    _ue_opts = [None] + _ues_list
                    _ue_cur  = next(
                        (i + 1 for i, u in enumerate(_ues_list)
                         if u["id"] == course.get("ue_id")), 0
                    )
                    _ucol, _ccol = st.columns([3, 1])
                    _sel_ue = _ucol.selectbox(
                        "Unité d'Enseignement (UE)",
                        _ue_opts, index=_ue_cur,
                        format_func=lambda u: (
                            "— Sans UE —" if u is None
                            else f"[{u.get('group_label','?')}] "
                                 f"{u.get('code','')} {u['name']}"
                        ),
                        key=f"ue_sel_{course['id']}"
                    )
                    _cred_ec = _ccol.number_input(
                        "Crédits EC",
                        value=float(course.get("credits_ec") or 1.0),
                        min_value=0.5, step=0.5,
                        key=f"cred_ec_{course['id']}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                CourseQueries.update(course["id"], nn, nc,
                                                     int(nh), float(nw))
                                if _sel_ue:
                                    _UQT.assign_course(course["id"],
                                                       _sel_ue["id"],
                                                       float(_cred_ec))
                                else:
                                    _UQT.unassign_course(course["id"])
                                st.success("✅ Cours mis à jour !"); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                CourseQueries.delete(course["id"])
                                st.success("✅ Cours supprimé."); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

        # ── Gestion des UE ────────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🎓 Unités d'Enseignement (UE)")
        st.caption(
            "Une UE regroupe plusieurs cours (EC). "
            "La note UE = moyenne pondérée des notes EC par leurs crédits. "
            "Le groupe (A, B…) sert au calcul des moyennes par groupe."
        )

        with st.expander("➕ Créer une UE"):
            with st.form("create_ue_form"):
                _unew_c1, _unew_c2, _unew_c3 = st.columns([2, 1, 1])
                _unew_name    = st.text_input("Intitulé * (ex: PHYSIOTHÉRAPIE 1)")
                _unew_code    = _unew_c1.text_input("Code (ex: PHY 101)")
                _unew_group   = _unew_c2.selectbox("Groupe", ["A","B","C","D","E","F"])
                _unew_credits = _unew_c3.number_input("Crédits UE", min_value=0.0,
                                                       max_value=50.0, value=0.0, step=0.5)
                if st.form_submit_button("✅ Créer", type="primary"):
                    if _unew_name.strip():
                        try:
                            _UQT.create(dept_id, _unew_name.strip(),
                                        _unew_code.strip() or None,
                                        float(_unew_credits), _unew_group)
                            st.success(f"✅ UE '{_unew_name.strip()}' créée !")
                            st.rerun()
                        except Exception as _e:
                            st.error(f"Erreur : {_e}")
                    else:
                        st.error("L'intitulé est obligatoire.")

        _GROUPS_CLR = {"A":"#2563EB","B":"#7C3AED","C":"#059669",
                       "D":"#D97706","E":"#DC2626","F":"#0891B2"}
        for _ue in _ues_list:
            _g_clr = _GROUPS_CLR.get(_ue.get("group_label","A"), "#64748B")
            _ec_n  = int(_ue.get("ec_count") or 0)
            with st.expander(
                f"🎓 [{_ue.get('group_label','?')}] "
                f"{_ue.get('code','')} — {_ue['name']} "
                f"· {int(_ue.get('credits',0))} crédits · {_ec_n} EC"
            ):
                with st.form(f"edit_ue_{_ue['id']}"):
                    _eu_n = st.text_input("Intitulé", value=_ue["name"])
                    _eu_c1, _eu_c2, _eu_c3 = st.columns([2, 1, 1])
                    _eu_code    = _eu_c1.text_input("Code", value=_ue.get("code",""))
                    _eu_group   = _eu_c2.selectbox(
                        "Groupe", ["A","B","C","D","E","F"],
                        index=(["A","B","C","D","E","F"].index(_ue.get("group_label","A"))
                               if _ue.get("group_label") in ["A","B","C","D","E","F"] else 0)
                    )
                    _eu_credits = _eu_c3.number_input(
                        "Crédits", value=float(_ue.get("credits") or 0),
                        min_value=0.0, step=0.5
                    )
                    _eu_b1, _eu_b2 = st.columns(2)
                    with _eu_b1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                _UQT.update(_ue["id"], _eu_n, _eu_code,
                                            float(_eu_credits), _eu_group)
                                st.success("✅ UE mise à jour !"); st.rerun()
                            except Exception as _e:
                                st.error(f"Erreur : {_e}")
                    with _eu_b2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                _UQT.delete(_ue["id"])
                                st.success("✅ UE supprimée."); st.rerun()
                            except Exception as _e:
                                st.error(f"Erreur : {_e}")

    # ── PROFESSEURS ───────────────────────────────────────────────────────────
    with tabs[3]:
        try:
            professors = ProfessorQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        st.metric("Professeurs", len(professors))
        st.divider()

        STATUTS = ["Contractuel", "Visiteur"]
        STATUT_ICONS = {"Contractuel": "🟢", "Visiteur": "🔵"}

        with st.expander("➕ Ajouter un professeur"):
            with st.form("add_prof"):
                name   = st.text_input("Nom complet *")
                email  = st.text_input("Email")
                phone  = st.text_input("Téléphone")
                statut = st.selectbox("Statut *", options=STATUTS)
                if st.form_submit_button("Ajouter", type="primary"):
                    if name.strip():
                        ProfessorQueries.create(name.strip(), email.strip(),
                                                phone.strip(), dept_id, statut)
                        st.success("✅ Professeur ajouté !"); st.rerun()
                    else:
                        st.error("Nom obligatoire.")

        for prof in professors:
            s_icon = STATUT_ICONS.get(prof.get("statut",""), "⚪")
            with st.expander(f"👨‍🏫 {prof['name']} — {s_icon} {prof.get('statut','—')}"):
                with st.form(f"edit_prof_{prof['id']}"):
                    nn  = st.text_input("Nom",       value=prof["name"])
                    ne  = st.text_input("Email",     value=prof.get("email",""))
                    nph = st.text_input("Téléphone", value=prof.get("phone",""))
                    ns  = st.selectbox("Statut", options=STATUTS,
                                       index=STATUTS.index(prof["statut"])
                                       if prof.get("statut") in STATUTS else 0)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                ProfessorQueries.update(prof["id"], nn, ne, nph, ns)
                                st.success("✅ Professeur mis à jour !"); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                ProfessorQueries.delete(prof["id"])
                                st.success("✅ Professeur supprimé."); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ── COMPTES PROFESSEURS ───────────────────────────────────────────────────
    with tabs[4]:
        from db.queries import ProfessorExtQueries
        from utils.auth import hash_password as _hp

        try:
            profs_with_account = ProfessorExtQueries.get_with_account(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); profs_with_account = []

        fac_id_dept  = dept.get("faculty_id") if dept else None
        uni_id_dept  = dept.get("university_id") if dept else user.get("university_id")

        st.metric("Professeurs avec compte", sum(1 for p in profs_with_account if p.get("user_id")))
        st.divider()

        if not profs_with_account:
            st.info("Aucun professeur dans ce département.")
        else:
            for prof in profs_with_account:
                has_account = bool(prof.get("user_id"))
                icon = "🟢" if has_account else "⚫"
                with st.expander(f"{icon} {prof['name']} — {'Compte actif' if has_account else 'Pas de compte'}"):
                    if has_account:
                        st.caption(f"Email de connexion : {prof.get('account_email','—')}")
                        if not prof.get("account_active"):
                            st.warning("Compte désactivé")
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.form(f"reset_prof_pwd_{prof['id']}"):
                                new_p  = st.text_input("Nouveau mot de passe *", type="password")
                                new_p2 = st.text_input("Confirmer *", type="password")
                                if st.form_submit_button("🔑 Réinitialiser"):
                                    if not new_p or len(new_p) < 8:
                                        st.error("Min 8 caractères.")
                                    elif new_p != new_p2:
                                        st.error("Mots de passe différents.")
                                    else:
                                        try:
                                            from db.queries import UserQueries as _UQ
                                            _UQ.update_password(prof["user_id"], _hp(new_p))
                                            st.success("✅ Mot de passe mis à jour !")
                                        except Exception as e:
                                            st.error(str(e))
                        with col2:
                            if st.button("⛔ Désactiver le compte",
                                         key=f"deact_prof_{prof['id']}"):
                                try:
                                    from db.queries import UserQueries as _UQ
                                    _UQ.deactivate(prof["user_id"])
                                    st.warning("Compte désactivé."); st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                    else:
                        st.caption("Ce professeur n'a pas encore de compte de connexion.")
                        with st.form(f"create_prof_account_{prof['id']}"):
                            pa_email = st.text_input("Email de connexion *",
                                                      value=prof.get("email",""))
                            pa_pwd   = st.text_input("Mot de passe * (min 8 car.)",
                                                      type="password")
                            pa_pwd2  = st.text_input("Confirmer *", type="password")
                            if st.form_submit_button("Créer le compte", type="primary"):
                                if not pa_email or "@" not in pa_email:
                                    st.error("Email invalide.")
                                elif not pa_pwd or len(pa_pwd) < 8:
                                    st.error("Min 8 caractères.")
                                elif pa_pwd != pa_pwd2:
                                    st.error("Mots de passe différents.")
                                else:
                                    try:
                                        from db.queries import UserQueries as _UQ
                                        existing = _UQ.get_by_email(pa_email.strip())
                                        if existing:
                                            st.error("Cet email est déjà utilisé.")
                                        else:
                                            _UQ.create_professor_account(
                                                name=prof["name"],
                                                email=pa_email.strip().lower(),
                                                password_hash=_hp(pa_pwd),
                                                university_id=uni_id_dept,
                                                faculty_id=fac_id_dept,
                                                department_id=dept_id,
                                                professor_id=prof["id"],
                                            )
                                            st.success(f"✅ Compte créé pour {prof['name']} !")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur : {e}")

    # ── EMPLOI DU TEMPS ───────────────────────────────────────────────────────
    with tabs[5]:
        import io as _io_sch
        import pandas as _pd_sch
        from datetime import timedelta as _td_sch, time as _time_sch, datetime as _dt_sch

        def _fmt_t(t) -> str:
            if t is None: return "--:--"
            if isinstance(t, _td_sch):
                h, m = divmod(int(t.total_seconds()) // 60, 60)
                return f"{h:02d}:{m:02d}"
            return str(t)[:5]

        def _to_time(t) -> "_time_sch":
            if isinstance(t, _time_sch): return t
            if isinstance(t, _td_sch):
                h, m = divmod(int(t.total_seconds()) // 60, 60)
                return _time_sch(h, m)
            try:
                parts = str(t)[:5].split(":")
                return _time_sch(int(parts[0]), int(parts[1]))
            except Exception:
                return _time_sch(8, 0)

        try:
            promotions = PromotionQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        if not promotions:
            st.info("Créez d'abord des promotions et classes.")
        else:
            promo_sel = st.selectbox("Promotion", options=promotions,
                                     format_func=lambda p: f"{p['name']} ({p['academic_year']})",
                                     key="sched_promo")
            if promo_sel:
                try:
                    classes = ClassQueries.get_by_promotion(promo_sel["id"])
                except Exception as e:
                    st.error(f"Erreur : {e}"); return

                if not classes:
                    st.info("Aucune salle dans cette promotion.")
                else:
                    cls_sel = st.selectbox("Salle", options=classes,
                                           format_func=lambda c: c["name"],
                                           key="sched_class")
                    if cls_sel:
                        try:
                            schedules  = ScheduleQueries.get_by_class(cls_sel["id"])
                            courses    = CourseQueries.get_by_department(dept_id)
                            uni_id_sch = (dept.get("university_id")
                                          or user.get("university_id"))
                            professors = ProfessorQueries.get_by_university(uni_id_sch)
                        except Exception as e:
                            st.error(f"Erreur : {e}"); return

                        DAYS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"]

                        # ── Barre d'actions : Export / Modèle ─────────────────
                        _ac1, _ac2, _ = st.columns([1, 1, 3])
                        with _ac1:
                            if schedules:
                                _rows_xls = [{
                                    "Jour":           s["day"],
                                    "Heure début":    _fmt_t(s["start_time"]),
                                    "Heure fin":      _fmt_t(s["end_time"]),
                                    "Type":           s.get("slot_type") or "cours",
                                    "Cours":          s["course_name"],
                                    "Professeur":     s["professor_name"],
                                    "Salle":          s.get("room") or "",
                                    "Semaine":        s.get("week_type","Toutes"),
                                    "Début validité": (s["valid_from"].strftime("%Y-%m-%d")
                                                       if s.get("valid_from") else ""),
                                    "Fin validité":   (s["valid_until"].strftime("%Y-%m-%d")
                                                       if s.get("valid_until") else ""),
                                } for s in schedules]
                                _buf_xls = _io_sch.BytesIO()
                                _pd_sch.DataFrame(_rows_xls).to_excel(
                                    _buf_xls, index=False, engine="openpyxl")
                                st.download_button(
                                    "📥 Exporter Excel",
                                    data=_buf_xls.getvalue(),
                                    file_name=f"EDT_{cls_sel['name'].replace(' ','_')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True,
                                )
                            else:
                                st.button("📥 Exporter Excel", disabled=True,
                                          use_container_width=True, key="exp_sched_dis")
                        with _ac2:
                            _buf_tmpl = _io_sch.BytesIO()
                            _pd_sch.DataFrame([{
                                "Jour": "Lundi", "Heure début": "08:00",
                                "Heure fin": "10:00", "Type": "cours",
                                "Cours": "Nom du cours",
                                "Professeur": "Nom du professeur", "Salle": "Salle A1",
                                "Semaine": "Toutes",
                                "Début validité": "2025-09-01",
                                "Fin validité":   "2026-01-31",
                            }, {
                                "Jour": "Mercredi", "Heure début": "09:00",
                                "Heure fin": "11:00", "Type": "examen",
                                "Cours": "Nom du cours", "Professeur": "Nom du prof",
                                "Salle": "Amphi B", "Semaine": "Toutes",
                                "Début validité": "", "Fin validité": "",
                            }, {
                                "Jour": "Vendredi", "Heure début": "00:00",
                                "Heure fin": "23:59", "Type": "ferie",
                                "Cours": "Fête nationale", "Professeur": "",
                                "Salle": "", "Semaine": "Toutes",
                                "Début validité": "", "Fin validité": "",
                            }]).to_excel(_buf_tmpl, index=False, engine="openpyxl")
                            st.download_button(
                                "📋 Modèle Excel",
                                data=_buf_tmpl.getvalue(),
                                file_name="modele_horaire.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )

                        # ── Import Excel ──────────────────────────────────────
                        with st.expander("📤 Importer depuis Excel"):
                            st.caption(
                                "Colonnes requises : **Jour · Heure début · Heure fin · "
                                "Type · Cours · Professeur · Salle · Semaine · "
                                "Début validité · Fin validité**  \n"
                                "Type accepté : `cours` · `examen` · `ferie`  \n"
                                "💡 Téléchargez le **Modèle Excel** ci-dessus pour le format exact."
                            )
                            _imp_run = st.session_state.get("imp_sched_run", 0)
                            _imp_file = st.file_uploader(
                                "Fichier Excel (.xlsx)", type=["xlsx"],
                                key=f"imp_sch_{cls_sel['id']}_{_imp_run}"
                            )
                            if _imp_file:
                                try:
                                    _df_raw = _pd_sch.read_excel(
                                        _imp_file, engine="openpyxl", dtype=str)
                                    _df_raw.columns = (
                                        _df_raw.columns.str.strip().str.lower()
                                        .str.replace("é","e",regex=False)
                                        .str.replace("è","e",regex=False)
                                        .str.replace(" ","_",regex=False)
                                    )
                                    _COL_MAP_S = {
                                        "jour":           "day",
                                        "heure_debut":    "start_time",
                                        "heure_fin":      "end_time",
                                        "type":           "slot_type_txt",
                                        "cours":          "course_txt",
                                        "professeur":     "professor_txt",
                                        "salle":          "room",
                                        "semaine":        "week_type",
                                        "debut_validite": "valid_from",
                                        "fin_validite":   "valid_until",
                                    }
                                    _REQUIRED_COLS = [c for c in _COL_MAP_S if c != "type"]
                                    _miss = [c for c in _REQUIRED_COLS
                                             if c not in _df_raw.columns]
                                    if _miss:
                                        st.error(
                                            f"Colonnes manquantes : **{', '.join(_miss)}**  \n"
                                            "Téléchargez le modèle pour vérifier le format.")
                                    else:
                                        _df_imp = _df_raw.rename(
                                            columns=_COL_MAP_S).fillna("")
                                        _imp_rows_data = _df_imp.to_dict("records")
                                        _nb = len(_imp_rows_data)

                                        _cbn = {c["name"].lower(): c for c in courses}
                                        _pbn = {p["name"].lower(): p for p in professors}

                                        def _best_c(txt):
                                            t = txt.lower()
                                            return next(
                                                (c for k,c in _cbn.items()
                                                 if t and (t in k or k in t)), None)

                                        def _best_p(txt):
                                            t = txt.lower()
                                            return next(
                                                (p for k,p in _pbn.items()
                                                 if t and (t in k or k in t)), None)

                                        st.markdown(
                                            f"**{_nb} ligne(s) détectée(s)** — "
                                            "Vérifiez et associez chaque créneau :")
                                        st.divider()

                                        _VALID_TYPES = ["cours","examen","ferie"]
                                        for _ri, _row in enumerate(_imp_rows_data):
                                            # Detect slot type from Excel column (optional)
                                            _raw_stype = str(_row.get("slot_type_txt","")).strip().lower()
                                            _stype_def = _raw_stype if _raw_stype in _VALID_TYPES else "cours"
                                            _styi = _VALID_TYPES.index(_stype_def)
                                            st.markdown(
                                                f"**Ligne {_ri+1}** — "
                                                f"{_row.get('day','')} "
                                                f"{_row.get('start_time','')}–"
                                                f"{_row.get('end_time','')} "
                                                f"· Salle : {_row.get('room') or '—'}"
                                            )
                                            _vt0, _vt1, _vt2 = st.columns([1,2,1])
                                            with _vt0:
                                                st.selectbox(
                                                    "Type *",
                                                    _VALID_TYPES,
                                                    format_func=lambda t: _TYPE_LABELS[t],
                                                    index=_styi,
                                                    key=f"imp_t_{_ri}")
                                            # Read current type for conditional fields
                                            _cur_imp_type = st.session_state.get(
                                                f"imp_t_{_ri}", _stype_def)
                                            with _vt1:
                                                if _cur_imp_type == "ferie":
                                                    st.text_input(
                                                        "Motif *",
                                                        value=_row.get("course_txt",""),
                                                        key=f"imp_c_{_ri}_lbl")
                                                else:
                                                    _prc = _best_c(_row.get("course_txt",""))
                                                    _ci0 = (courses.index(_prc)
                                                            if _prc and _prc in courses else 0)
                                                    st.selectbox(
                                                        "Cours *", options=courses,
                                                        format_func=lambda c: c["name"],
                                                        index=_ci0,
                                                        key=f"imp_c_{_ri}")
                                            with _vt2:
                                                if _cur_imp_type != "ferie":
                                                    _prp = _best_p(_row.get("professor_txt",""))
                                                    _pi0 = (professors.index(_prp)
                                                            if _prp and _prp in professors else 0)
                                                    st.selectbox(
                                                        "Professeur *", options=professors,
                                                        format_func=lambda p: p["name"],
                                                        index=_pi0,
                                                        key=f"imp_p_{_ri}")
                                            _vc3, _vd1, _vd2, _vd3 = st.columns([1,1,2,2])
                                            with _vc3:
                                                _wtr = _row.get("week_type","Toutes")
                                                _wti = (["Toutes","Paire","Impaire"].index(_wtr)
                                                        if _wtr in ["Toutes","Paire","Impaire"]
                                                        else 0)
                                                st.selectbox(
                                                    "Semaine",
                                                    ["Toutes","Paire","Impaire"],
                                                    index=_wti,
                                                    key=f"imp_w_{_ri}")
                                            _vd1, _vd2, _vd3 = st.columns([1,2,2])
                                            with _vd1:
                                                _dr = _row.get("day","Lundi")
                                                _di = DAYS.index(_dr) if _dr in DAYS else 0
                                                st.selectbox("Jour", DAYS, index=_di,
                                                             key=f"imp_d_{_ri}")
                                            with _vd2:
                                                _vf_v = None
                                                try:
                                                    _vf_v = _dt_sch.strptime(
                                                        str(_row.get("valid_from",""))[:10],
                                                        "%Y-%m-%d").date()
                                                except Exception:
                                                    pass
                                                st.date_input("Début validité",
                                                              value=_vf_v,
                                                              key=f"imp_vf_{_ri}")
                                            with _vd3:
                                                _vu_v = None
                                                try:
                                                    _vu_v = _dt_sch.strptime(
                                                        str(_row.get("valid_until",""))[:10],
                                                        "%Y-%m-%d").date()
                                                except Exception:
                                                    pass
                                                st.date_input("Fin validité",
                                                              value=_vu_v,
                                                              key=f"imp_vu_{_ri}")
                                            st.divider()

                                        if st.button("✅ Confirmer l'import",
                                                     type="primary",
                                                     key="confirm_sched_import"):
                                            _ok_c = _err_c = 0
                                            for _ri, _row in enumerate(_imp_rows_data):
                                                try:
                                                    _simp_type = st.session_state.get(
                                                        f"imp_t_{_ri}", "cours")
                                                    _swt = st.session_state.get(
                                                        f"imp_w_{_ri}", "Toutes")
                                                    _sd  = st.session_state.get(
                                                        f"imp_d_{_ri}",
                                                        _row.get("day","Lundi"))
                                                    _svf = st.session_state.get(f"imp_vf_{_ri}")
                                                    _svu = st.session_state.get(f"imp_vu_{_ri}")
                                                    _sst = str(_row.get("start_time","08:00"))[:5]
                                                    _sen = str(_row.get("end_time","09:00"))[:5]
                                                    _srm = str(_row.get("room","")).strip()
                                                    if _simp_type == "ferie":
                                                        _lbl = str(st.session_state.get(
                                                            f"imp_c_{_ri}_lbl",
                                                            _row.get("course_txt",""))).strip()
                                                        ScheduleQueries.create(
                                                            cls_sel["id"], _sd, _sst, _sen,
                                                            _srm, None, None, _swt,
                                                            valid_from=_svf if _svf else None,
                                                            valid_until=_svu if _svu else None,
                                                            slot_type="ferie",
                                                            slot_label=_lbl or None,
                                                        )
                                                    else:
                                                        _sc = st.session_state.get(f"imp_c_{_ri}")
                                                        _sp = st.session_state.get(f"imp_p_{_ri}")
                                                        if not _sc or not _sp:
                                                            _err_c += 1; continue
                                                        ScheduleQueries.create(
                                                            cls_sel["id"], _sd, _sst, _sen,
                                                            _srm, _sc["id"], _sp["id"], _swt,
                                                            valid_from=_svf if _svf else None,
                                                            valid_until=_svu if _svu else None,
                                                            slot_type=_simp_type,
                                                        )
                                                    _ok_c += 1
                                                except Exception:
                                                    _err_c += 1
                                            if _ok_c > 0:
                                                st.success(
                                                    f"✅ {_ok_c} créneau(x) importé(s)"
                                                    + (f" · {_err_c} erreur(s)"
                                                       if _err_c else ""))
                                                st.session_state["imp_sched_run"] = _imp_run + 1
                                                st.rerun()
                                            else:
                                                st.error(
                                                    f"Aucun créneau importé. {_err_c} erreur(s).")
                                except Exception as _exc:
                                    st.error(f"Erreur lecture Excel : {_exc}")

                        st.divider()

                        # ── Grille visuelle ───────────────────────────────────
                        st.markdown("#### Grille actuelle")
                        render_schedule_table(schedules)
                        st.divider()

                        # ── Ajouter un créneau ────────────────────────────────
                        _TYPE_LABELS = {
                            "cours":  "📚 Cours",
                            "examen": "📝 Examen",
                            "ferie":  "🚫 Férié / Congé",
                        }
                        _WT_LABELS = {"Toutes": "Toutes", "Paire": "Semaine 2", "Impaire": "Semaine 1"}
                        with st.expander("➕ Ajouter un créneau"):
                            # ── Type (HORS form pour rerender immédiat) ──────────
                            st.markdown("**🎯 Type de créneau**")
                            _add_type = st.radio(
                                "Type",
                                list(_TYPE_LABELS.keys()),
                                format_func=lambda t: _TYPE_LABELS[t],
                                horizontal=True,
                                key="add_sched_type_sel",
                                label_visibility="collapsed",
                            )
                            # ── Période : seulement pour cours ───────────────────
                            if _add_type == "cours":
                                _use_period_add = st.checkbox(
                                    "📅 Définir une période de validité (semestre / trimestre)",
                                    key="use_period_add")
                            else:
                                _use_period_add = False
                            st.divider()
                            if _add_type != "ferie" and not courses:
                                st.info("Créez d'abord des cours.")
                            elif _add_type != "ferie" and not professors:
                                st.info("Ajoutez d'abord des professeurs.")
                            else:
                                with st.form("add_schedule"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        days       = st.multiselect(
                                            "Jour(s) *", DAYS,
                                            placeholder="Sélectionner un ou plusieurs jours")
                                        start_time = st.time_input("Heure début *")
                                        end_time   = st.time_input("Heure fin *")
                                        if _add_type == "cours":
                                            week_type = st.selectbox(
                                                "Semaine", ["Toutes","Paire","Impaire"],
                                                format_func=lambda w: _WT_LABELS[w])
                                        else:
                                            week_type = "Toutes"
                                    with col2:
                                        _add_label = None
                                        _add_course = None
                                        _add_prof   = None
                                        if _add_type == "ferie":
                                            _add_label = st.text_input(
                                                "Motif *",
                                                placeholder="ex: Fête nationale")
                                        else:
                                            _add_course = st.selectbox(
                                                "Cours *", options=courses,
                                                format_func=lambda c: c["name"])
                                            _add_prof = st.selectbox(
                                                "Professeur *", options=professors,
                                                format_func=lambda p: f"{p['name']} · {p.get('statut','—')} ({p.get('department_name','—')})")
                                        room = st.text_input("Salle")
                                    # ── Date(s) selon le type ────────────────────
                                    if _add_type in ("examen", "ferie"):
                                        sched_valid_from = st.date_input(
                                            "📅 Date *", key="sched_single_date")
                                        sched_valid_until = sched_valid_from
                                    elif _use_period_add:
                                        _vfc2, _vuc2 = st.columns(2)
                                        with _vfc2:
                                            sched_valid_from = st.date_input(
                                                "Début de période", key="sched_vf")
                                        with _vuc2:
                                            sched_valid_until = st.date_input(
                                                "Fin de période", key="sched_vu")
                                    else:
                                        sched_valid_from = sched_valid_until = None
                                        st.caption("♻️ Récurrent toute l'année — cochez ci-dessus pour limiter à une période.")
                                    if st.form_submit_button("Ajouter", type="primary"):
                                        if not days:
                                            st.error("Sélectionnez au moins un jour.")
                                        elif start_time >= end_time:
                                            st.error("L'heure de fin doit être après l'heure de début.")
                                        elif (_add_type == "ferie"
                                              and not (_add_label or "").strip()):
                                            st.error("Le motif est obligatoire pour un jour férié.")
                                        elif (sched_valid_from and sched_valid_until
                                              and sched_valid_from > sched_valid_until):
                                            st.error("La date de fin doit être après la date de début.")
                                        else:
                                            _ss = start_time.strftime("%H:%M")
                                            _es = end_time.strftime("%H:%M")
                                            _ok_days, _conf_days = [], []
                                            try:
                                                for _day in days:
                                                    if (_add_type == "cours"
                                                            and ScheduleQueries.check_conflict(
                                                                cls_sel["id"], _day, _ss, _es)):
                                                        _conf_days.append(_day)
                                                        continue
                                                    # Check professor and room conflicts (warnings only)
                                                    _prof_conf = (ScheduleQueries.check_professor_conflict(
                                                        _add_prof["id"], _day, _ss, _es) if _add_prof else [])
                                                    _room_conf = (ScheduleQueries.check_room_conflict(
                                                        room.strip(), _day, _ss, _es) if room.strip() else [])
                                                    ScheduleQueries.create(
                                                        cls_sel["id"], _day, _ss, _es,
                                                        room.strip(),
                                                        _add_course["id"] if _add_course else None,
                                                        _add_prof["id"]   if _add_prof   else None,
                                                        week_type,
                                                        valid_from=sched_valid_from or None,
                                                        valid_until=sched_valid_until or None,
                                                        slot_type=_add_type,
                                                        slot_label=(_add_label or "").strip() or None,
                                                    )
                                                    _ok_days.append(_day)
                                                    _warns = []
                                                    if _prof_conf:
                                                        _warns.append(f"Prof déjà occupé(e) dans : {', '.join(r['class_name'] for r in _prof_conf)}")
                                                    if _room_conf:
                                                        _warns.append(f"Salle déjà utilisée par : {', '.join(r['class_name'] for r in _room_conf)}")
                                                    for _w in _warns:
                                                        st.warning(f"⚠️ {_day} — {_w}")
                                                if _ok_days:
                                                    _msg = f"✅ {len(_ok_days)} créneau(x) ajouté(s) : {', '.join(_ok_days)}"
                                                    if _conf_days:
                                                        _msg += f"  ⚠️ Conflit ignoré : {', '.join(_conf_days)}"
                                                    st.success(_msg); st.rerun()
                                                else:
                                                    st.error("⚠️ Conflit d'horaire sur tous les jours sélectionnés.")
                                            except Exception as e:
                                                st.error(f"Erreur : {e}")

                        # ── Créneaux existants : édition directe ──────────────
                        if schedules:
                            st.markdown("#### ✏️ Modifier les créneaux existants")
                            _TYPE_COLORS = {
                                "cours":  "#2563EB",
                                "examen": "#16A34A",
                                "ferie":  "#DC2626",
                            }
                            _TYPE_ICONS = {
                                "cours": "📚", "examen": "📝", "ferie": "🚫"
                            }
                            for s in schedules:
                                _ek     = f"sched_edit_{s['id']}"
                                _is_ed  = st.session_state.get(_ek, False)
                                _vf     = s.get("valid_from")
                                _vu     = s.get("valid_until")
                                _wt     = s.get("week_type","Toutes")
                                _stype  = s.get("slot_type","cours")
                                _period = (
                                    " · ♻️ Récurrent" if not _vf and not _vu
                                    else f" · 📅 {_vf.strftime('%d/%m') if _vf else '…'}"
                                         f"→ {_vu.strftime('%d/%m') if _vu else '…'}"
                                )
                                _wt_b   = f" · **{_wt}**" if _wt != "Toutes" else ""
                                _tc     = _TYPE_COLORS.get(_stype,"#2563EB")
                                _ti     = _TYPE_ICONS.get(_stype,"📚")
                                _label  = (
                                    f"<span style='color:{_tc};font-weight:700'>{_ti}</span> "
                                    f"{s['day']} {_fmt_t(s['start_time'])}–"
                                    f"{_fmt_t(s['end_time'])} | "
                                    f"<b>{s['course_name']}</b>"
                                    + (f" | {s['professor_name']}" if s.get("professor_name") else "")
                                    + f"{_wt_b}{_period}"
                                )
                                _cl1, _cl2, _cl3 = st.columns([5, 1, 1])
                                _cl1.markdown(
                                    f"<div style='padding:0.35rem 0;font-size:0.82rem;"
                                    f"color:#475569'>{_label}</div>",
                                    unsafe_allow_html=True)
                                with _cl2:
                                    if st.button(
                                        "✏️" if not _is_ed else "✕",
                                        key=f"tog_ed_{s['id']}",
                                        help="Modifier" if not _is_ed else "Annuler",
                                    ):
                                        st.session_state[_ek] = not _is_ed
                                        st.rerun()
                                with _cl3:
                                    if st.button("🗑️", key=f"del_sched_{s['id']}",
                                                 help="Supprimer ce créneau"):
                                        ScheduleQueries.delete(s["id"])
                                        st.success("Créneau supprimé."); st.rerun()

                                if _is_ed:
                                    _ci    = next((i for i,c in enumerate(courses)
                                                   if c["id"]==s.get("course_id")), 0)
                                    _pi    = next((i for i,p in enumerate(professors)
                                                   if p["id"]==s.get("professor_id")), 0)
                                    _wt_i  = (["Toutes","Paire","Impaire"].index(_wt)
                                              if _wt in ["Toutes","Paire","Impaire"] else 0)
                                    _day_i = DAYS.index(s["day"]) if s["day"] in DAYS else 0
                                    _st_opts = ["cours","examen","ferie"]
                                    _st_i    = (_st_opts.index(_stype)
                                                if _stype in _st_opts else 0)

                                    with st.container(border=True):
                                        # ── Type (HORS form) ─────────────────────
                                        st.markdown("**🎯 Type de créneau**")
                                        _e_stype = st.radio(
                                            "Type",
                                            _st_opts,
                                            format_func=lambda t: _TYPE_LABELS[t],
                                            index=_st_i,
                                            horizontal=True,
                                            key=f"ed_type_{s['id']}",
                                            label_visibility="collapsed",
                                        )
                                        # ── Période/date selon type (HORS form) ──────
                                        if _e_stype == "cours":
                                            _has_period = bool(_vf or _vu)
                                            _use_period_ed = st.checkbox(
                                                "📅 Période de validité",
                                                value=_has_period,
                                                key=f"use_period_ed_{s['id']}")
                                        else:
                                            _use_period_ed = False

                                        with st.form(f"edit_sched_{s['id']}"):
                                            _ef1, _ef2 = st.columns(2)
                                            with _ef1:
                                                _e_day   = st.selectbox(
                                                    "Jour *", DAYS, index=_day_i,
                                                    key=f"ed_day_{s['id']}")
                                                _e_start = st.time_input(
                                                    "Heure début *",
                                                    value=_to_time(s["start_time"]),
                                                    key=f"ed_st_{s['id']}")
                                                _e_end   = st.time_input(
                                                    "Heure fin *",
                                                    value=_to_time(s["end_time"]),
                                                    key=f"ed_en_{s['id']}")
                                                if _e_stype == "cours":
                                                    _e_wt = st.selectbox(
                                                        "Semaine",
                                                        ["Toutes","Paire","Impaire"],
                                                        format_func=lambda w: _WT_LABELS[w],
                                                        index=_wt_i,
                                                        key=f"ed_wt_{s['id']}")
                                                else:
                                                    _e_wt = "Toutes"
                                            with _ef2:
                                                _e_label  = None
                                                _e_course = None
                                                _e_prof   = None
                                                if _e_stype == "ferie":
                                                    _e_label = st.text_input(
                                                        "Motif *",
                                                        value=s.get("slot_label") or "",
                                                        key=f"ed_lbl_{s['id']}")
                                                else:
                                                    _e_course = st.selectbox(
                                                        "Cours *", options=courses,
                                                        format_func=lambda c: c["name"],
                                                        index=_ci,
                                                        key=f"ed_c_{s['id']}")
                                                    _e_prof = st.selectbox(
                                                        "Professeur *", options=professors,
                                                        format_func=lambda p: f"{p['name']} · {p.get('statut','—')}",
                                                        index=_pi,
                                                        key=f"ed_p_{s['id']}")
                                                _e_room = st.text_input(
                                                    "Salle",
                                                    value=s.get("room") or "",
                                                    key=f"ed_rm_{s['id']}")
                                            # ── Date selon le type ───────────────
                                            if _e_stype in ("examen", "ferie"):
                                                _e_vf = st.date_input(
                                                    "📅 Date *",
                                                    value=_vf if _vf else None,
                                                    key=f"ed_vf_{s['id']}")
                                                _e_vu = _e_vf
                                            elif _use_period_ed:
                                                _evf_c, _evu_c = st.columns(2)
                                                with _evf_c:
                                                    _e_vf = st.date_input(
                                                        "Début de période",
                                                        value=_vf if _vf else None,
                                                        key=f"ed_vf_{s['id']}")
                                                with _evu_c:
                                                    _e_vu = st.date_input(
                                                        "Fin de période",
                                                        value=_vu if _vu else None,
                                                        key=f"ed_vu_{s['id']}")
                                            else:
                                                _e_vf = _e_vu = None
                                                st.caption("♻️ Récurrent toute l'année.")
                                            _fs1, _fs2 = st.columns(2)
                                            with _fs1:
                                                if st.form_submit_button(
                                                        "💾 Sauvegarder", type="primary"):
                                                    if _e_start >= _e_end:
                                                        st.error(
                                                            "Heure fin > heure début requise.")
                                                    elif (_e_stype == "ferie"
                                                          and not (_e_label or "").strip()):
                                                        st.error("Le motif est obligatoire.")
                                                    else:
                                                        try:
                                                            ScheduleQueries.update(
                                                                s["id"],
                                                                _e_day,
                                                                _e_start.strftime("%H:%M"),
                                                                _e_end.strftime("%H:%M"),
                                                                _e_room.strip(),
                                                                _e_course["id"] if _e_course else None,
                                                                _e_prof["id"]   if _e_prof   else None,
                                                                _e_wt,
                                                                valid_from=_e_vf if _e_vf else None,
                                                                valid_until=_e_vu if _e_vu else None,
                                                                slot_type=_e_stype,
                                                                slot_label=(_e_label or "").strip() or None,
                                                            )
                                                            st.session_state[_ek] = False
                                                            st.success("✅ Créneau mis à jour !")
                                                            st.rerun()
                                                        except Exception as _ex:
                                                            st.error(f"Erreur : {_ex}")
                                            with _fs2:
                                                if st.form_submit_button("❌ Annuler"):
                                                    st.session_state[_ek] = False
                                                    st.rerun()

                                        # ── Statut du créneau ────────────────
                                        st.divider()
                                        st.markdown("**Statut du créneau**")
                                        _cur_status = s.get("slot_status", "actif")
                                        _status_opts = {
                                            "actif":   "Actif",
                                            "annule":  "Annulé",
                                            "remplace": "Remplacé",
                                        }
                                        with st.form(f"status_form_{s['id']}"):
                                            _new_status = st.selectbox(
                                                "Statut",
                                                list(_status_opts.keys()),
                                                format_func=lambda x: _status_opts[x],
                                                index=list(_status_opts.keys()).index(
                                                    _cur_status if _cur_status in _status_opts else "actif"),
                                            )
                                            _status_note = st.text_input(
                                                "Note (raison)",
                                                value=s.get("cancel_note") or "")
                                            _sub_prof = None
                                            if _new_status == "remplace":
                                                _sub_i = next(
                                                    (i for i, p in enumerate(professors)
                                                     if p["id"] == s.get("substitute_professor_id")), 0)
                                                _sub_prof = st.selectbox(
                                                    "Professeur remplaçant",
                                                    professors,
                                                    format_func=lambda p: p["name"],
                                                    index=_sub_i)
                                            if st.form_submit_button("Appliquer le statut"):
                                                ScheduleQueries.set_status(
                                                    s["id"], _new_status, _status_note,
                                                    _sub_prof["id"] if _sub_prof else None)
                                                # Notify students
                                                try:
                                                    from utils.notifications import notify_schedule_change
                                                    from db.connection import execute_query as _eq2
                                                    _stud_emails = [
                                                        st2["email"]
                                                        for st2 in (_eq2(
                                                            "SELECT email FROM students WHERE class_id=%s AND is_active=TRUE",
                                                            (cls_sel["id"],)) or [])
                                                        if st2.get("email")
                                                    ]
                                                    if _stud_emails:
                                                        notify_schedule_change(
                                                            cls_sel["name"], s["day"],
                                                            str(s["start_time"])[:5],
                                                            s["course_name"], _new_status,
                                                            _status_note, _stud_emails)
                                                except Exception:
                                                    pass
                                                st.success("Statut mis à jour !")
                                                st.rerun()

                                        # ── Historique des modifications ──────
                                        with st.expander("Historique des modifications"):
                                            try:
                                                _hist = ScheduleQueries.get_audit(s["id"])
                                            except Exception:
                                                _hist = []
                                            if not _hist:
                                                st.caption("Aucune modification enregistrée.")
                                            else:
                                                for h in _hist:
                                                    _hat = h.get("changed_at")
                                                    _hat_str = (_hat.strftime("%d/%m/%Y %H:%M")
                                                                if _hat else "—")
                                                    st.caption(
                                                        f"{_hat_str} — **{h['action']}** "
                                                        f"par {h.get('changed_by','—')}")

                        # ── Dupliquer l'horaire ───────────────────────────────
                        with st.expander("Dupliquer vers une autre salle"):
                            _all_classes_dup = ClassQueries.get_by_promotion(promo_sel["id"])
                            _other_cls = [c for c in _all_classes_dup if c["id"] != cls_sel["id"]]
                            if not _other_cls:
                                st.info("Aucune autre salle dans cette promotion.")
                            else:
                                _dup_target = st.selectbox(
                                    "Salle cible", _other_cls,
                                    format_func=lambda c: c["name"],
                                    key="dup_target_cls")
                                if st.button("Dupliquer", type="primary", key="btn_dup"):
                                    _n = ScheduleQueries.duplicate_schedules(
                                        cls_sel["id"], _dup_target["id"])
                                    st.success(f"✅ {_n} créneau(x) copié(s) vers {_dup_target['name']}")
                                    st.rerun()

                        # ── Analytiques du département ────────────────────────
                        with st.expander("Analytiques du département"):
                            try:
                                import pandas as _pd_analytics
                                _stats = ScheduleQueries.get_stats(dept_id)
                                if _stats:
                                    _sc1, _sc2, _sc3, _sc4 = st.columns(4)
                                    _sc1.metric("Créneaux actifs", _stats["total_slots"] or 0)
                                    _sc2.metric("Professeurs",     _stats["total_profs"] or 0)
                                    _sc3.metric("Cours",           _stats["total_courses"] or 0)
                                    _sc4.metric("Heures totales",  f"{round(float(_stats['total_hours'] or 0), 1)}h")
                                    st.divider()
                                _ph = ScheduleQueries.get_professor_hours(dept_id)
                                if _ph:
                                    st.markdown("**Heures par professeur**")
                                    st.dataframe(
                                        _pd_analytics.DataFrame(_ph)[["name", "nb_slots", "total_hours"]]
                                        .rename(columns={"name": "Professeur",
                                                         "nb_slots": "Créneaux",
                                                         "total_hours": "Heures"}),
                                        use_container_width=True, hide_index=True)
                                _ru = ScheduleQueries.get_room_usage(dept_id)
                                if _ru:
                                    st.markdown("**Utilisation des salles**")
                                    st.dataframe(
                                        _pd_analytics.DataFrame(_ru)[["room", "nb_slots", "total_hours"]]
                                        .rename(columns={"room": "Salle",
                                                         "nb_slots": "Créneaux",
                                                         "total_hours": "Heures"}),
                                        use_container_width=True, hide_index=True)
                            except Exception as _ae:
                                st.caption(f"Analytiques indisponibles : {_ae}")

    # ── COMMUNIQUÉS ───────────────────────────────────────────────────────────
    with tabs[6]:
        try:
            announcements = AnnouncementQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        st.metric("Communiqués actifs", len(announcements))
        st.divider()

        with st.expander("➕ Publier un communiqué"):
            with st.form("add_ann"):
                title     = st.text_input("Titre *")
                content   = st.text_area("Contenu *")
                is_pinned = st.checkbox("📌 Épingler en haut")
                expires   = st.date_input("Date d'expiration (optionnel)", value=None)
                ann_file  = st.file_uploader(
                    "Fichier joint — PDF ou image (optionnel)",
                    type=["pdf", "jpg", "jpeg", "png", "gif", "webp"],
                    key="ann_file_upload"
                )
                if st.form_submit_button("Publier", type="primary"):
                    if title.strip() and content.strip():
                        expires_dt = None
                        if expires:
                            from datetime import datetime
                            expires_dt = datetime.combine(expires, datetime.max.time())
                        file_url = file_name = None
                        if ann_file:
                            try:
                                from utils.storage import upload_file, ANNOUNCEMENTS_BUCKET
                                file_url, _ = upload_file(
                                    ann_file.read(), ann_file.name,
                                    ANNOUNCEMENTS_BUCKET,
                                    folder=f"dept_{dept_id}"
                                )
                                file_name = ann_file.name
                            except Exception as _e:
                                st.warning(f"Fichier non uploadé : {_e}")
                        AnnouncementQueries.create(
                            title.strip(), content.strip(), dept_id,
                            is_pinned, expires_dt, file_url, file_name)
                        st.success("✅ Communiqué publié !")
                        try:
                            from utils.notifications import notify_announcement_dept
                            uni_name_ann  = dept.get("university_name", "") if dept else ""
                            dept_name_ann = dept["name"] if dept else ""
                            sent = notify_announcement_dept(
                                dept_id, title.strip(), content.strip(),
                                uni_name_ann, dept_name_ann)
                            if sent > 0:
                                st.info(f"📧 {sent} notification(s) email envoyée(s).")
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error("Titre et contenu obligatoires.")

        for ann in announcements:
            with st.expander(f"{'📌 ' if ann.get('is_pinned') else ''}📢 {ann['title']}"):
                announcement_card(ann)
                if st.button("🗑️ Supprimer", key=f"del_ann_{ann['id']}"):
                    AnnouncementQueries.delete(ann["id"])
                    st.success("✅ Communiqué supprimé."); st.rerun()

    # ── REGISTRE ÉTUDIANTS (Liste d'inscription) ─────────────────────────────
    with tabs[7]:
        import io
        import pandas as pd
        from db.queries import (StudentRegistryQueries, ClassQueries as _CQ,
                                PromotionQueries as _PQ,
                                FiliereQueries as _FQ, OptionEtudeQueries as _OQ,
                                FacultyQueries as _FacQ, DepartmentQueries as _DQ2)

        uni_id_for_reg = user.get("university_id")

        try:
            registry = StudentRegistryQueries.get_by_university(uni_id_for_reg)
        except Exception as e:
            st.error(f"Erreur : {e}"); registry = []

        registered_count = sum(1 for r in registry if r.get("is_registered"))
        c1r, c2r, c3r, c4r = st.columns(4)
        c1r.metric("Total registre",  len(registry))
        c2r.metric("Comptes créés",   registered_count)
        c3r.metric("En attente",      len(registry) - registered_count)
        _annees_reg = StudentRegistryQueries.get_annees_academiques(uni_id_for_reg)
        c4r.metric("Années académiques", len(_annees_reg))
        st.divider()

        # ── Filtres d'affichage et d'export ──────────────────────────────────
        st.markdown("#### Filtrer / Exporter la liste")
        _f1, _f2, _f3, _f4 = st.columns(4)
        with _f1:
            _fil_annee = st.selectbox(
                "Année académique", ["Toutes"] + _annees_reg,
                key="reg_fil_annee"
            )
        try:
            _filieres_reg = _FQ.get_by_department(dept_id) or []
        except Exception:
            _filieres_reg = []
        with _f2:
            _fil_filiere = st.selectbox(
                "Filière", [None] + _filieres_reg,
                format_func=lambda f: "Toutes" if f is None else f["name"],
                key="reg_fil_filiere"
            )
        try:
            _options_reg = (_OQ.get_by_filiere(_fil_filiere["id"])
                            if _fil_filiere else [])
        except Exception:
            _options_reg = []
        with _f3:
            _fil_option = st.selectbox(
                "Option", [None] + _options_reg,
                format_func=lambda o: "Toutes" if o is None else o["name"],
                key="reg_fil_option"
            )
        try:
            _promos_reg = _PQ.get_by_department(dept_id) or []
        except Exception:
            _promos_reg = []
        with _f4:
            _fil_promo = st.selectbox(
                "Promotion", [None] + _promos_reg,
                format_func=lambda p: "Toutes" if p is None else p["name"],
                key="reg_fil_promo"
            )

        # Appliquer les filtres
        _reg_filtered = list(registry)
        if _fil_annee != "Toutes":
            _reg_filtered = [r for r in _reg_filtered
                             if r.get("annee_academique") == _fil_annee]
        if _fil_filiere:
            _reg_filtered = [r for r in _reg_filtered
                             if r.get("filiere_id") == _fil_filiere["id"]]
        if _fil_option:
            _reg_filtered = [r for r in _reg_filtered
                             if r.get("option_id") == _fil_option["id"]]
        if _fil_promo:
            _reg_filtered = [r for r in _reg_filtered
                             if r.get("promotion_id") == _fil_promo["id"]]

        st.caption(f"**{len(_reg_filtered)}** étudiant(s) correspondant(s)")

        # ── Export template + liste filtrée ───────────────────────────────────
        col_tmpl, col_exp = st.columns(2)
        with col_tmpl:
            df_tmpl = pd.DataFrame(columns=[
                "numéro étudiant", "nom", "postnom", "prénom",
                "école de provenance", "date de naissance (AAAA-MM-JJ)", "sexe (M/F)"
            ])
            buf_tmpl = io.BytesIO()
            df_tmpl.to_excel(buf_tmpl, index=False, engine="openpyxl")
            st.download_button(
                "📥 Modèle d'import Excel",
                data=buf_tmpl.getvalue(),
                file_name="modele_inscription.xlsx",
                mime=("application/vnd.openxmlformats-officedocument"
                      ".spreadsheetml.sheet"),
                use_container_width=True,
            )
        with col_exp:
            if _reg_filtered:
                _exp_rows = [{
                    "numéro étudiant":   r["student_number"],
                    "nom":               r.get("nom") or r.get("full_name",""),
                    "postnom":           r.get("postnom") or "",
                    "prénom":            r.get("prenom") or "",
                    "département":       r.get("department_name") or r.get("promotion_txt") or "",
                    "filière":           r.get("filiere_name") or "",
                    "option":            r.get("option_name") or r.get("option_txt") or "",
                    "promotion":         r.get("promotion_name") or r.get("promotion_txt") or "",
                    "année académique":  r.get("annee_academique") or "",
                    "école de provenance": r.get("ecole_provenance") or "",
                    "compte créé":       "Oui" if r.get("is_registered") else "Non",
                } for r in _reg_filtered]
                _buf_exp = io.BytesIO()
                pd.DataFrame(_exp_rows).to_excel(
                    _buf_exp, index=False, engine="openpyxl")
                _fn_exp = (
                    f"inscription_"
                    f"{(_fil_filiere['name'] if _fil_filiere else 'tout')}".replace(" ","_")
                    + f"_{_fil_annee if _fil_annee != 'Toutes' else 'toutes_annees'}.xlsx"
                )
                st.download_button(
                    "📤 Exporter la liste filtrée (.xlsx)",
                    data=_buf_exp.getvalue(),
                    file_name=_fn_exp,
                    mime=("application/vnd.openxmlformats-officedocument"
                          ".spreadsheetml.sheet"),
                    use_container_width=True,
                )
            else:
                st.button("📤 Exporter", disabled=True,
                          use_container_width=True)

        st.divider()

        # ── Import Excel (avec contexte filière/option/promotion) ─────────────
        with st.expander("📂 Importer depuis Excel"):
            st.caption(
                "Sélectionnez d'abord le contexte (filière, option, promotion, année). "
                "Le fichier Excel n'a besoin que des colonnes : "
                "**numéro étudiant · nom · postnom · prénom** "
                "(+ école de provenance, date de naissance, sexe en option)."
            )

            _ic1, _ic2 = st.columns(2)
            with _ic1:
                _imp_fac_list = []
                try:
                    _imp_fac_list = _FacQ.get_by_university(uni_id_for_reg) or []
                except Exception:
                    pass
                _imp_fac = st.selectbox(
                    "Faculté *", [None] + _imp_fac_list,
                    format_func=lambda f: "— Sélectionner —" if f is None else f["name"],
                    key="imp_fac"
                )
            with _ic2:
                _imp_dept_list = _DQ2.get_by_faculty(_imp_fac["id"]) if _imp_fac else []
                _imp_dept = st.selectbox(
                    "Département *", [None] + _imp_dept_list,
                    format_func=lambda d: "— Sélectionner —" if d is None else d["name"],
                    key="imp_dept"
                )

            _ic3, _ic4 = st.columns(2)
            with _ic3:
                _imp_fi_list = _FQ.get_by_department(_imp_dept["id"]) if _imp_dept else []
                _imp_fi = st.selectbox(
                    "Filière", [None] + _imp_fi_list,
                    format_func=lambda f: "— (optionnel) —" if f is None else f["name"],
                    key="imp_filiere"
                )
            with _ic4:
                _imp_opt_list = _OQ.get_by_filiere(_imp_fi["id"]) if _imp_fi else []
                _imp_opt = st.selectbox(
                    "Option", [None] + _imp_opt_list,
                    format_func=lambda o: "— (optionnel) —" if o is None else o["name"],
                    key="imp_option"
                )

            _ic5, _ic6 = st.columns(2)
            with _ic5:
                _imp_pr_list = _PQ.get_by_department(_imp_dept["id"]) if _imp_dept else []
                _imp_pr = st.selectbox(
                    "Promotion", [None] + _imp_pr_list,
                    format_func=lambda p: "— (optionnel) —" if p is None else p["name"],
                    key="imp_promo_ctx"
                )
            with _ic6:
                _imp_annee = st.text_input(
                    "Année académique *",
                    value=_current_ay["label"] if _current_ay else "",
                    placeholder="ex: 2024-2025",
                    key="imp_annee_ctx"
                )

            _imp_cls_list = (_CQ.get_by_promotion(_imp_pr["id"])
                             if _imp_pr else [])
            _imp_cls = st.selectbox(
                "Assigner à une classe (optionnel)", [None] + _imp_cls_list,
                format_func=lambda c: "— Aucune —" if c is None else c["name"],
                key="imp_cls_ctx"
            ) if _imp_cls_list else None

            excel_file = st.file_uploader(
                "Fichier Excel (.xlsx)", type=["xlsx"], key="import_registry_excel"
            )
            if excel_file:
                try:
                    df_raw = pd.read_excel(excel_file, engine="openpyxl", dtype=str)
                    df_raw.columns = (
                        df_raw.columns.str.strip().str.lower()
                        .str.replace("é","e", regex=False)
                        .str.replace("è","e", regex=False)
                        .str.replace("ê","e", regex=False)
                        .str.replace("ô","o", regex=False)
                        .str.replace(" ","_", regex=False)
                    )
                    _req_cols = ["numero_etudiant", "nom"]
                    _missing_c = [c for c in _req_cols if c not in df_raw.columns]
                    if _missing_c:
                        st.error(
                            f"Colonnes manquantes : **{', '.join(_missing_c)}**  \n"
                            "Téléchargez le modèle pour voir le format exact."
                        )
                    else:
                        df_import = df_raw.fillna("")
                        st.markdown("**Aperçu (5 premières lignes) :**")
                        _preview_cols = [c for c in
                                         ["numero_etudiant","nom","postnom","prenom",
                                          "ecole_de_provenance"]
                                         if c in df_import.columns]
                        st.dataframe(df_import[_preview_cols].head(5),
                                     use_container_width=True, hide_index=True)
                        st.caption(f"Total détecté : **{len(df_import)}** lignes")

                        if not _imp_annee.strip():
                            st.warning("Saisissez l'année académique avant d'importer.")
                        elif not _imp_dept:
                            st.warning("Sélectionnez au moins un département.")
                        elif st.button("✅ Confirmer l'import", type="primary",
                                       key="confirm_import_excel"):
                            inserted = skipped = errors = 0
                            for _, row in df_import.iterrows():
                                num = str(row.get("numero_etudiant","")).strip().upper()
                                if not num:
                                    errors += 1; continue
                                try:
                                    n_v  = str(row.get("nom","")).strip()
                                    pn_v = str(row.get("postnom","")).strip()
                                    pr_v = str(row.get("prenom","")).strip()
                                    ec_v = str(row.get("ecole_de_provenance","")).strip()
                                    dn_v = str(row.get("date_de_naissance_aaaa_mm_jj","")).strip() or None
                                    sx_v = str(row.get("sexe_m_f","")).strip().upper() or None
                                    full = " ".join(filter(None,[pr_v,n_v,pn_v])) or n_v
                                    StudentRegistryQueries.create_full(
                                        student_number=num,
                                        full_name=full,
                                        university_id=uni_id_for_reg,
                                        class_id=_imp_cls["id"] if _imp_cls else None,
                                        nom=n_v or None,
                                        postnom=pn_v or None,
                                        prenom=pr_v or None,
                                        promotion_txt=_imp_pr["name"] if _imp_pr else None,
                                        option_txt=_imp_opt["name"] if _imp_opt else None,
                                        department_id=_imp_dept["id"] if _imp_dept else None,
                                        filiere_id=_imp_fi["id"] if _imp_fi else None,
                                        option_id=_imp_opt["id"] if _imp_opt else None,
                                        promotion_id=_imp_pr["id"] if _imp_pr else None,
                                        annee_academique=_imp_annee.strip(),
                                        ecole_provenance=ec_v or None,
                                        date_naissance=dn_v,
                                        sexe=sx_v,
                                    )
                                    inserted += 1
                                except Exception as exc:
                                    if "unique" in str(exc).lower():
                                        skipped += 1
                                    else:
                                        errors += 1
                            st.success(
                                f"✅ Import terminé — "
                                f"**{inserted}** insérés · "
                                f"**{skipped}** doublons ignorés · "
                                f"**{errors}** erreurs"
                            )
                            st.rerun()
                except Exception as e:
                    st.error(f"Erreur lecture Excel : {e}")

        # ── Ajouter manuellement ──────────────────────────────────────────────
        with st.expander("➕ Ajouter un étudiant manuellement"):
            _m1, _m2 = st.columns(2)
            with _m1:
                _man_fac_list = []
                try:
                    _man_fac_list = _FacQ.get_by_university(uni_id_for_reg) or []
                except Exception:
                    pass
                _man_fac = st.selectbox(
                    "Faculté", [None] + _man_fac_list,
                    format_func=lambda f: "— Sélectionner —" if f is None else f["name"],
                    key="man_fac"
                )
            with _m2:
                _man_dept_list = _DQ2.get_by_faculty(_man_fac["id"]) if _man_fac else []
                _man_dept = st.selectbox(
                    "Département", [None] + _man_dept_list,
                    format_func=lambda d: "— Sélectionner —" if d is None else d["name"],
                    key="man_dept"
                )

            _m3, _m4 = st.columns(2)
            with _m3:
                _man_fi_list = _FQ.get_by_department(_man_dept["id"]) if _man_dept else []
                _man_fi = st.selectbox(
                    "Filière", [None] + _man_fi_list,
                    format_func=lambda f: "— (optionnel) —" if f is None else f["name"],
                    key="man_filiere"
                )
            with _m4:
                _man_opt_list = _OQ.get_by_filiere(_man_fi["id"]) if _man_fi else []
                _man_opt = st.selectbox(
                    "Option", [None] + _man_opt_list,
                    format_func=lambda o: "— (optionnel) —" if o is None else o["name"],
                    key="man_option"
                )

            _m5, _m6 = st.columns(2)
            with _m5:
                _man_pr_list = _PQ.get_by_department(_man_dept["id"]) if _man_dept else []
                _man_pr = st.selectbox(
                    "Promotion", [None] + _man_pr_list,
                    format_func=lambda p: "— (optionnel) —" if p is None else p["name"],
                    key="man_promo_ctx"
                )
            with _m6:
                _man_cls_list = (_CQ.get_by_promotion(_man_pr["id"])
                                 if _man_pr else [])
                _man_cls = st.selectbox(
                    "Classe", [None] + _man_cls_list,
                    format_func=lambda c: "— Aucune —" if c is None else c["name"],
                    key="man_cls_ctx"
                ) if _man_cls_list else None

            with st.form("add_student_registry"):
                _reg_annee = st.text_input(
                    "Année académique *",
                    value=_current_ay["label"] if _current_ay else "",
                    placeholder="ex: 2024-2025",
                    key="man_annee_form"
                )
                reg_num = st.text_input("Numéro étudiant *",
                                        placeholder="ex: 2024001234")
                col_n, col_pn, col_pr = st.columns(3)
                with col_n:
                    reg_nom     = st.text_input("Nom *",    placeholder="ex: DUPONT")
                with col_pn:
                    reg_postnom = st.text_input("Postnom",  placeholder="ex: KABILA")
                with col_pr:
                    reg_prenom  = st.text_input("Prénom",   placeholder="ex: Marie")

                col_ec, col_sx = st.columns(2)
                with col_ec:
                    reg_ecole = st.text_input("École de provenance",
                                              placeholder="ex: Lycée Saint-Joseph")
                with col_sx:
                    reg_sexe = st.selectbox("Sexe", ["", "M", "F", "Autre"])

                if st.form_submit_button("Ajouter au registre", type="primary"):
                    if not reg_num.strip() or not reg_nom.strip():
                        st.error("Numéro étudiant et nom obligatoires.")
                    elif not _reg_annee.strip():
                        st.error("L'année académique est obligatoire.")
                    else:
                        try:
                            full = " ".join(filter(None, [
                                reg_prenom.strip(), reg_nom.strip(),
                                reg_postnom.strip()
                            ])) or reg_nom.strip()
                            StudentRegistryQueries.create_full(
                                student_number=reg_num,
                                full_name=full,
                                university_id=uni_id_for_reg,
                                class_id=_man_cls["id"] if _man_cls else None,
                                nom=reg_nom.strip() or None,
                                postnom=reg_postnom.strip() or None,
                                prenom=reg_prenom.strip() or None,
                                promotion_txt=_man_pr["name"] if _man_pr else None,
                                option_txt=_man_opt["name"] if _man_opt else None,
                                department_id=_man_dept["id"] if _man_dept else None,
                                filiere_id=_man_fi["id"] if _man_fi else None,
                                option_id=_man_opt["id"] if _man_opt else None,
                                promotion_id=_man_pr["id"] if _man_pr else None,
                                annee_academique=_reg_annee.strip(),
                                ecole_provenance=reg_ecole.strip() or None,
                                sexe=reg_sexe or None,
                            )
                            st.success(f"✅ {reg_num.upper()} ajouté au registre !")
                            st.rerun()
                        except Exception as e:
                            if "unique" in str(e).lower():
                                st.error("Ce numéro étudiant existe déjà dans le registre.")
                            else:
                                st.error(f"Erreur : {e}")

        # ── Liste du registre ─────────────────────────────────────────────────
        from db.queries import StudentQueries as _SQReg
        from utils.auth import hash_password as _hp_reg

        _STATUT_OPTS = {
            "inscrit":    "📋 Inscrit",
            "admis":      "✅ Admis(e)",
            "redoublant": "🔄 Redoublant(e)",
            "transfere":  "↗️ Transféré(e)",
            "abandonne":  "❌ Abandonné(e)",
        }
        _STATUT_COLORS = {
            "inscrit":    "#3B82F6",
            "admis":      "#10B981",
            "redoublant": "#F59E0B",
            "transfere":  "#8B5CF6",
            "abandonne":  "#EF4444",
        }

        st.divider()
        st.markdown(f"#### Liste d'inscription ({len(_reg_filtered)} étudiant(s))")
        if not _reg_filtered:
            st.info("Aucun étudiant correspondant aux filtres sélectionnés.")
        else:
            for reg in _reg_filtered:
                _has_account = bool(reg.get("is_registered"))
                _statut_val  = reg.get("statut") or "inscrit"
                _statut_lbl  = _STATUT_OPTS.get(_statut_val, _statut_val)
                _statut_clr  = _STATUT_COLORS.get(_statut_val, "#64748B")
                _acc_icon    = "✅" if _has_account else "⚪"
                nom_display  = " ".join(filter(None, [
                    reg.get("prenom",""), reg.get("nom",""), reg.get("postnom","")
                ])) or reg.get("full_name","—")
                _dept_lbl = reg.get("department_name") or "—"
                _fi_lbl   = reg.get("filiere_name") or reg.get("promotion_txt") or "—"
                _opt_lbl  = reg.get("option_name") or reg.get("option_txt") or "—"
                _pr_lbl   = reg.get("promotion_name") or "—"
                _yr_lbl   = reg.get("annee_academique") or "—"
                with st.expander(
                    f"{_acc_icon} **{reg['student_number']}** — {nom_display}  "
                    f"·  {_statut_lbl}  ·  {_yr_lbl}"
                ):
                    ca, cb, cc, cd = st.columns(4)
                    ca.markdown(f"**Département**  \n{_dept_lbl}")
                    cb.markdown(f"**Filière / Option**  \n{_fi_lbl} / {_opt_lbl}")
                    cc.markdown(f"**Promotion**  \n{_pr_lbl}")
                    cd.markdown(f"**Année acad.**  \n{_yr_lbl}")
                    _ecole = reg.get("ecole_provenance")
                    _sexe  = reg.get("sexe")
                    if _ecole or _sexe:
                        _parts = []
                        if _ecole: _parts.append(f"École : {_ecole}")
                        if _sexe:  _parts.append(f"Sexe : {_sexe}")
                        st.caption("  ·  ".join(_parts))

                    # ── Statut académique ─────────────────────────────────────
                    _st_col, _st_btn = st.columns([3, 1])
                    _new_statut = _st_col.selectbox(
                        "Statut académique",
                        options=list(_STATUT_OPTS.keys()),
                        index=list(_STATUT_OPTS.keys()).index(_statut_val)
                              if _statut_val in _STATUT_OPTS else 0,
                        format_func=lambda s: _STATUT_OPTS[s],
                        key=f"statut_sel_{reg['id']}",
                    )
                    with _st_btn:
                        st.write("")
                        st.write("")
                        if st.button("💾 Sauver", key=f"save_statut_{reg['id']}",
                                     use_container_width=True):
                            StudentRegistryQueries.update_statut(reg["id"], _new_statut)
                            st.success("Statut mis à jour."); st.rerun()

                    st.divider()

                    # ── Compte étudiant ───────────────────────────────────────
                    if _has_account:
                        _stu_id     = reg.get("student_account_id")
                        _stu_uname  = reg.get("student_username") or "—"
                        _stu_active = reg.get("student_is_active", True)
                        _state_lbl  = "🟢 Actif" if _stu_active else "🔴 Désactivé"
                        _ca1, _ca2, _ca3 = st.columns([3, 1, 1])
                        _ca1.markdown(
                            f"**Compte :** ✅ @{_stu_uname} &nbsp; {_state_lbl}"
                        )
                        with _ca2:
                            if _stu_active:
                                if st.button("⛔ Désactiver",
                                             key=f"deact_reg_{reg['id']}",
                                             use_container_width=True):
                                    _SQReg.set_active(_stu_id, False); st.rerun()
                            else:
                                if st.button("✅ Activer",
                                             key=f"act_reg_{reg['id']}",
                                             type="primary",
                                             use_container_width=True):
                                    _SQReg.set_active(_stu_id, True); st.rerun()
                        with _ca3:
                            if st.button("🔑 Réinit. MDP",
                                         key=f"rst_reg_{reg['id']}",
                                         use_container_width=True):
                                st.session_state[f"show_reset_{reg['id']}"] = True
                        if st.session_state.get(f"show_reset_{reg['id']}"):
                            with st.form(f"reset_pwd_reg_{reg['id']}"):
                                _np = st.text_input("Nouveau mot de passe",
                                                    type="password",
                                                    key=f"np_reg_{reg['id']}")
                                if st.form_submit_button("Confirmer"):
                                    if _np.strip():
                                        _SQReg.reset_password(_stu_id, _hp_reg(_np))
                                        st.session_state.pop(f"show_reset_{reg['id']}", None)
                                        st.success("Mot de passe réinitialisé."); st.rerun()
                                    else:
                                        st.error("Mot de passe vide.")
                    else:
                        # Pas encore de compte — formulaire de création
                        st.markdown("**Compte :** ⚪ Aucun compte — créer l'accès :")
                        with st.form(f"create_acc_reg_{reg['id']}"):
                            _uc, _pc = st.columns(2)
                            _new_uname = _uc.text_input(
                                "Nom d'utilisateur",
                                value=reg["student_number"].lower(),
                                key=f"uname_reg_{reg['id']}"
                            )
                            _new_pwd = _pc.text_input(
                                "Mot de passe", type="password",
                                key=f"pwd_reg_{reg['id']}"
                            )
                            _new_email = st.text_input(
                                "Email (optionnel)",
                                key=f"email_reg_{reg['id']}"
                            )
                            if st.form_submit_button("🔑 Créer le compte", type="primary"):
                                if not _new_pwd.strip():
                                    st.error("Mot de passe obligatoire.")
                                else:
                                    try:
                                        _fn = " ".join(filter(None, [
                                            reg.get("prenom",""), reg.get("nom",""),
                                            reg.get("postnom","")
                                        ])) or reg.get("full_name","")
                                        _SQReg.create(
                                            student_number=reg["student_number"],
                                            full_name=_fn,
                                            email=_new_email.strip() or None,
                                            password_hash=_hp_reg(_new_pwd),
                                            class_id=reg.get("class_id"),
                                            university_id=reg["university_id"],
                                            registry_id=reg["id"],
                                            nom=reg.get("nom"),
                                            postnom=reg.get("postnom"),
                                            prenom=reg.get("prenom"),
                                            username=_new_uname.strip(),
                                        )
                                        st.success(f"✅ Compte créé !"); st.rerun()
                                    except Exception as _ce:
                                        if "unique" in str(_ce).lower():
                                            st.error("Ce numéro / nom d'utilisateur existe déjà.")
                                        else:
                                            st.error(f"Erreur : {_ce}")

                    # ── Supprimer du registre ─────────────────────────────────
                    st.divider()
                    if st.button("🗑️ Retirer du registre",
                                 key=f"del_reg_{reg['id']}"):
                        StudentRegistryQueries.delete(reg["id"])
                        st.success("Retiré du registre."); st.rerun()

    # ── COMPTES ÉTUDIANTS (gestion uniquement) ────────────────────────────────
    with tabs[8]:
        from db.queries import StudentQueries as _SQ
        from utils.auth import hash_password as _hp_stu

        try:
            all_students = _SQ.get_by_department(dept_id)
        except Exception as e:
            st.error(str(e)); all_students = []

        actifs_stu   = [s for s in all_students if s.get("is_active")]
        inactifs_stu = [s for s in all_students if not s.get("is_active")]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total comptes",  len(all_students))
        c2.metric("Actifs",         len(actifs_stu))
        c3.metric("Désactivés",     len(inactifs_stu))
        st.info(
            "Les comptes étudiants se créent depuis **Registre Étudiants** "
            "(onglet précédent) — sélectionnez un inscrit sans compte et cliquez "
            "« 🔑 Créer le compte »."
        )
        st.divider()

        search_stu = st.text_input("🔍 Rechercher", placeholder="Nom ou numéro...",
                                   key="search_stu_dept")

        for stu in all_students:
            if search_stu and search_stu.lower() not in stu["full_name"].lower() \
                          and search_stu.lower() not in stu["student_number"].lower():
                continue

            is_active = stu.get("is_active", True)
            icon = "✅" if is_active else "⛔"
            with st.expander(
                f"{icon} {stu['full_name']} — N° {stu['student_number']} "
                f"· {stu.get('promotion_name','—')} / {stu.get('class_name','—')}"
            ):
                st.caption(
                    f"👤 @{stu.get('username','—')} · "
                    f"📧 {stu.get('email','—')}"
                )
                _sb1, _sb2, _sb3 = st.columns(3)
                with _sb1:
                    if is_active:
                        if st.button("⛔ Désactiver",
                                     key=f"deact_stu_{stu['id']}",
                                     use_container_width=True):
                            _SQ.set_active(stu["id"], False); st.rerun()
                    else:
                        if st.button("✅ Activer",
                                     key=f"act_stu_{stu['id']}",
                                     type="primary",
                                     use_container_width=True):
                            _SQ.set_active(stu["id"], True); st.rerun()
                with _sb2:
                    if st.button("🔑 Réinit. MDP",
                                 key=f"rst_stu_{stu['id']}",
                                 use_container_width=True):
                        st.session_state[f"show_rst_stu_{stu['id']}"] = True
                if st.session_state.get(f"show_rst_stu_{stu['id']}"):
                    with st.form(f"rst_stu_form_{stu['id']}"):
                        _np2 = st.text_input("Nouveau mot de passe", type="password",
                                             key=f"np_stu_{stu['id']}")
                        if st.form_submit_button("Confirmer"):
                            if _np2.strip():
                                _SQ.reset_password(stu["id"], _hp_stu(_np2))
                                st.session_state.pop(f"show_rst_stu_{stu['id']}", None)
                                st.success("Mot de passe réinitialisé."); st.rerun()
                            else:
                                st.error("Mot de passe vide.")

    # ── RÉSULTATS D'EXAMENS ───────────────────────────────────────────────────
    with tabs[9]:
        import io as _io
        import pandas as _pd
        from db.queries import (GradeQueries as _GQR,
                                ClassQueries as _CQR2,
                                PromotionQueries as _PQR2)

        def _mention(avg):
            if avg >= 18: return "Excellent"
            if avg >= 16: return "Très Bien"
            if avg >= 14: return "Bien"
            if avg >= 12: return "Assez Bien"
            if avg >= 10: return "Passable"
            return "Non admis"

        def _decision(avg, t_admis=10.0, t_sess2=7.0):
            if avg >= t_admis: return "Admis"
            if avg >= t_sess2: return "Session 2"
            return "Ajourné"

        st.markdown("#### Résultats d'examens par promotion")
        st.caption("Visualisez, publiez et exportez les bulletins d'une promotion.")

        try:
            promotions_res = _PQR2.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); promotions_res = []

        if not promotions_res:
            st.info("Créez d'abord des promotions et assurez-vous que des notes existent.")
        else:
            col_pr, col_cl = st.columns(2)
            with col_pr:
                promo_res = st.selectbox(
                    "Promotion", options=promotions_res,
                    format_func=lambda p: f"{p['name']} ({p['academic_year']})",
                    key="res_promo"
                )

            classes_res = _CQR2.get_by_promotion(promo_res["id"]) if promo_res else []
            with col_cl:
                if not classes_res:
                    st.info("Aucune classe dans cette promotion.")
                    class_res = None
                else:
                    class_res = st.selectbox(
                        "Classe", options=classes_res,
                        format_func=lambda c: c["name"],
                        key="res_class"
                    )

            if class_res:
                try:
                    sessions_res = _GQR.get_sessions_by_class(class_res["id"])
                except Exception:
                    sessions_res = []

                session_names_res = [s["session_name"] for s in (sessions_res or [])]

                col_ss, col_ns = st.columns([2, 1])
                with col_ss:
                    if session_names_res:
                        session_sel_res = st.selectbox(
                            "Session existante", options=session_names_res,
                            key="res_session_sel"
                        )
                    else:
                        session_sel_res = None
                        st.caption("Aucune session disponible pour cette classe.")
                with col_ns:
                    new_session_res = st.text_input(
                        "Ou saisir une session",
                        placeholder="ex: Janvier 2025",
                        key="res_new_session"
                    )

                active_session_res = (new_session_res.strip()
                                      if new_session_res.strip()
                                      else session_sel_res)

                if not active_session_res:
                    st.info("Sélectionnez ou saisissez une session pour afficher les résultats.")
                else:
                    st.markdown(f"**Session : {active_session_res}**")

                    # ── Seuils de décision ────────────────────────────────────
                    with st.expander("⚙️ Seuils de décision", expanded=False):
                        _tc1, _tc2 = st.columns(2)
                        _thr_admis = _tc1.slider(
                            "Seuil Admis (≥ X/20)",
                            min_value=5.0, max_value=20.0, value=10.0,
                            step=0.5, key="res_thr_admis"
                        )
                        _thr_sess2 = _tc2.slider(
                            "Seuil Session 2 (≥ X/20)",
                            min_value=0.0, max_value=float(_thr_admis),
                            value=min(7.0, float(_thr_admis)),
                            step=0.5, key="res_thr_sess2"
                        )
                        _dc1, _dc2, _dc3 = st.columns(3)
                        _dc1.markdown(
                            f"<div style='padding:0.5rem;background:#D1FAE522;"
                            f"border:1px solid #059669;border-radius:8px;text-align:center'>"
                            f"<b style='color:#059669'>✅ Admis</b><br>"
                            f"<span style='font-size:0.8rem'>≥ {_thr_admis}/20</span></div>",
                            unsafe_allow_html=True)
                        _dc2.markdown(
                            f"<div style='padding:0.5rem;background:#FEF3C722;"
                            f"border:1px solid #F59E0B;border-radius:8px;text-align:center'>"
                            f"<b style='color:#D97706'>⚠️ Session 2</b><br>"
                            f"<span style='font-size:0.8rem'>{_thr_sess2}–{_thr_admis}/20</span></div>",
                            unsafe_allow_html=True)
                        _dc3.markdown(
                            f"<div style='padding:0.5rem;background:#FEE2E222;"
                            f"border:1px solid #EF4444;border-radius:8px;text-align:center'>"
                            f"<b style='color:#EF4444'>❌ Ajourné</b><br>"
                            f"<span style='font-size:0.8rem'>< {_thr_sess2}/20</span></div>",
                            unsafe_allow_html=True)

                    st.divider()

                    try:
                        grades_res = _GQR.get_by_class_session(
                            class_res["id"], active_session_res)
                    except Exception as e:
                        st.error(f"Erreur : {e}"); grades_res = []

                    if not grades_res:
                        st.info("Aucune note enregistrée pour cette session.")
                    else:
                        # ── Construire les résultats par étudiant ─────────────
                        by_student_r = {}
                        courses_w = {}  # course_name → weight

                        for g in grades_res:
                            sid = g["student_id"]
                            if sid not in by_student_r:
                                by_student_r[sid] = {
                                    "name": g["student_name"],
                                    "number": g["student_number"],
                                    "by_course": {},
                                }
                            cn = g["course_name"]
                            courses_w[cn] = float(g.get("course_weight") or 1.0)
                            norm = (g["grade"] / g["max_grade"] * 20
                                    if g.get("max_grade") else 0.0)
                            by_student_r[sid]["by_course"].setdefault(cn, []).append(norm)

                        course_list_r = sorted(courses_w.keys())
                        results_r = []
                        for sid, data in by_student_r.items():
                            c_avgs = {}
                            for cn in course_list_r:
                                vals = data["by_course"].get(cn)
                                c_avgs[cn] = sum(vals) / len(vals) if vals else None

                            total_w = sum(courses_w[cn]
                                          for cn in course_list_r
                                          if c_avgs.get(cn) is not None)
                            total_wg = sum(c_avgs[cn] * courses_w[cn]
                                           for cn in course_list_r
                                           if c_avgs.get(cn) is not None)
                            avg_r = total_wg / total_w if total_w > 0 else 0.0

                            results_r.append({
                                "student_id": sid,
                                "Nom": data["name"],
                                "N°": data["number"],
                                "_avg": avg_r,
                                **{cn: (f"{c_avgs[cn]:.1f}"
                                        if c_avgs[cn] is not None else "—")
                                   for cn in course_list_r},
                            })

                        results_r.sort(key=lambda x: x["_avg"], reverse=True)
                        for i, r in enumerate(results_r):
                            r["Rang"] = i + 1
                            r["Moyenne"] = f"{r['_avg']:.2f}/20"
                            r["Mention"] = _mention(r["_avg"])
                            r["Décision"] = _decision(r["_avg"], _thr_admis, _thr_sess2)

                        # ── Tableau de résultats ──────────────────────────────
                        df_cols_r = (["Rang", "Nom", "N°"] + course_list_r
                                     + ["Moyenne", "Mention", "Décision"])
                        df_res = _pd.DataFrame(
                            [{k: r.get(k, "—") for k in df_cols_r}
                             for r in results_r]
                        )
                        st.dataframe(df_res, use_container_width=True,
                                     hide_index=True)

                        st.divider()

                        # ── Statut du workflow ────────────────────────────────
                        from db.queries import BulletinQueries as _BQR
                        try:
                            _sum_rows_admin = _GQR.get_status_summary(
                                class_res["id"], active_session_res) or []
                            _status_admin = {r["status"]: int(r["cnt"])
                                             for r in _sum_rows_admin}
                        except Exception:
                            _status_admin = {}

                        _A_CLR = {"brouillon":"#64748B","soumis":"#3B82F6",
                                  "valide":"#10B981","publie":"#6D28D9"}
                        _A_LBL = {"brouillon":"Brouillon","soumis":"Soumis",
                                  "valide":"Validé","publie":"Publié"}

                        if _status_admin:
                            _sa_cols = st.columns(min(4, len(_status_admin)))
                            for _si, (_ss, _sc_cnt) in enumerate(_status_admin.items()):
                                _sc_ = _A_CLR.get(_ss, "#64748B")
                                _sl_ = _A_LBL.get(_ss, _ss)
                                _sa_cols[_si].markdown(
                                    f"<div style='text-align:center;padding:0.5rem;"
                                    f"background:{_sc_}15;border:1px solid {_sc_}44;"
                                    f"border-radius:8px'>"
                                    f"<div style='font-size:0.72rem;color:{_sc_};"
                                    f"font-weight:600'>{_sl_}</div>"
                                    f"<div style='font-size:1.5rem;font-weight:700;"
                                    f"color:{_sc_}'>{_sc_cnt}</div>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

                        _nb_brouillon_a = _status_admin.get("brouillon", 0)
                        _nb_soumis_a    = _status_admin.get("soumis",    0)
                        _nb_valide_a    = _status_admin.get("valide",    0)
                        _nb_publie_a    = _status_admin.get("publie",    0)
                        _all_publie     = (_nb_publie_a > 0
                                           and _nb_brouillon_a == 0
                                           and _nb_soumis_a == 0
                                           and _nb_valide_a == 0)

                        # ── Actions ───────────────────────────────────────────
                        col_val_r, col_pub_r, col_calc_r, col_exp_r = st.columns([1, 1, 1, 2])

                        with col_val_r:
                            _can_validate = (_nb_brouillon_a + _nb_soumis_a) > 0
                            if _can_validate and not _all_publie:
                                if st.button("✔️ Valider les notes",
                                             key="res_validate_btn"):
                                    try:
                                        _GQR.validate_session(
                                            class_res["id"], active_session_res)
                                        # Créer/mettre à jour le bulletin en mode 'valide'
                                        _acad_yr = (promo_res.get("academic_year","")
                                                    if promo_res else "")
                                        _BQR.upsert(class_res["id"], active_session_res,
                                                    _acad_yr, created_by=user["id"])
                                        _BQR.validate(class_res["id"], active_session_res,
                                                      _acad_yr, validated_by=user["id"])
                                        st.success(
                                            "✅ Notes validées. Vous pouvez "
                                            "maintenant les publier.")
                                        st.rerun()
                                    except Exception as _ev:
                                        st.error(f"Erreur : {_ev}")

                        with col_pub_r:
                            if _all_publie:
                                st.success("✅ Session publiée")
                            elif (_nb_valide_a + _nb_soumis_a + _nb_brouillon_a) > 0:
                                if st.button("📢 Publier les résultats",
                                             type="primary",
                                             key="res_publish_btn"):
                                    try:
                                        _GQR.publish_session(
                                            class_res["id"], active_session_res)
                                        # Mettre à jour le bulletin
                                        _acad_yr = (promo_res.get("academic_year","")
                                                    if promo_res else "")
                                        _BQR.upsert(class_res["id"], active_session_res,
                                                    _acad_yr, created_by=user["id"])
                                        _BQR.publish(class_res["id"], active_session_res,
                                                     _acad_yr, published_by=user["id"])
                                        from utils.notifications import notify_session_published
                                        _uni_pub = (dept.get("university_name","UniSchedule")
                                                    if dept else "UniSchedule")
                                        _sent = notify_session_published(
                                            grades_res, active_session_res, _uni_pub)
                                        _msg = "✅ Résultats publiés !"
                                        if _sent:
                                            _msg += f" 📧 {_sent} étudiant(s) notifié(s)."
                                        st.success(_msg); st.rerun()
                                    except Exception as _ep:
                                        st.error(f"Erreur : {_ep}")

                        with col_calc_r:
                            from db.queries import StudentResultsQueries as _SRRQ
                            if st.button("🧮 Calculer les décisions",
                                         key="res_compute_btn",
                                         use_container_width=True):
                                try:
                                    _acad_yr_c = (promo_res.get("academic_year","")
                                                  if promo_res else "")
                                    for _r in results_r:
                                        _SRRQ.upsert(
                                            student_id      = _r["student_id"],
                                            class_id        = class_res["id"],
                                            session_name    = active_session_res,
                                            academic_year   = _acad_yr_c,
                                            average         = round(_r["_avg"], 2),
                                            rank            = _r["Rang"],
                                            decision        = _r["Décision"],
                                            threshold_admis = _thr_admis,
                                            threshold_session2 = _thr_sess2,
                                            computed_by     = user["id"],
                                        )
                                    _nb_admis   = sum(1 for _r in results_r if _r["Décision"] == "Admis")
                                    _nb_sess2   = sum(1 for _r in results_r if _r["Décision"] == "Session 2")
                                    _nb_ajourn  = sum(1 for _r in results_r if _r["Décision"] == "Ajourné")
                                    st.success(
                                        f"✅ Décisions enregistrées — "
                                        f"Admis : {_nb_admis} · "
                                        f"Session 2 : {_nb_sess2} · "
                                        f"Ajournés : {_nb_ajourn}"
                                    )
                                except Exception as _ec:
                                    st.error(f"Erreur : {_ec}")

                        with col_exp_r:
                            buf_r = _io.BytesIO()
                            df_res.to_excel(buf_r, index=False, engine="openpyxl")
                            fname_r = (f"resultats_"
                                       f"{class_res['name'].replace(' ','_')}_"
                                       f"{active_session_res.replace(' ','_')}.xlsx")
                            st.download_button(
                                "📥 Exporter Excel",
                                data=buf_r.getvalue(),
                                file_name=fname_r,
                                mime=("application/vnd.openxmlformats-officedocument"
                                      ".spreadsheetml.sheet"),
                                use_container_width=True,
                            )

                        # ── Calcul résultats par UE ───────────────────────────
                        _has_ue_r = any(g.get("ue_id") for g in grades_res)
                        if _has_ue_r:
                            st.divider()
                            st.markdown("##### 🎓 Résultats par Unité d'Enseignement")
                            _thr_ue_r = st.slider(
                                "Seuil validation UE (≥ X/20)",
                                min_value=5.0, max_value=15.0,
                                value=10.0, step=0.5,
                                key="res_thr_ue"
                            )
                            if st.button("🎓 Calculer les résultats UE",
                                         key="btn_ue_calc", type="primary"):
                                from db.queries import StudentUEResultsQueries as _SURQ2
                                _by_stu_ue = {}
                                for _g in grades_res:
                                    _sid = _g["student_id"]
                                    _uid = _g.get("ue_id")
                                    if not _uid:
                                        continue
                                    _by_stu_ue.setdefault(_sid, {})
                                    if _uid not in _by_stu_ue[_sid]:
                                        _by_stu_ue[_sid][_uid] = {
                                            "ue_credits": float(_g.get("ue_credits") or 0),
                                            "ec": {},
                                        }
                                    _cid = _g["course_id"]
                                    _by_stu_ue[_sid][_uid]["ec"].setdefault(
                                        _cid, {
                                            "credits_ec": float(_g.get("credits_ec") or 1),
                                            "exams": [],
                                        }
                                    )
                                    _norm_g = (_g["grade"] / _g["max_grade"] * 20
                                               if _g.get("max_grade") else 0)
                                    _by_stu_ue[_sid][_uid]["ec"][_cid]["exams"].append(_norm_g)

                                _acad_yr_ue = (promo_res.get("academic_year","")
                                               if promo_res else "")
                                _n_ue_saved = 0
                                for _sid, _ue_dict in _by_stu_ue.items():
                                    for _uid, _ue_d in _ue_dict.items():
                                        _tw = _twg = 0
                                        for _ec in _ue_d["ec"].values():
                                            _ea = (sum(_ec["exams"]) / len(_ec["exams"])
                                                   if _ec["exams"] else 0)
                                            _tw  += _ec["credits_ec"]
                                            _twg += _ea * _ec["credits_ec"]
                                        _note_ue = _twg / _tw if _tw > 0 else 0
                                        _dec_ue  = "V" if _note_ue >= _thr_ue_r else "NV"
                                        _cred_obt = (_ue_d["ue_credits"]
                                                     if _dec_ue == "V" else 0)
                                        try:
                                            _SURQ2.upsert(
                                                student_id       = _sid,
                                                ue_id            = _uid,
                                                session_name     = active_session_res,
                                                academic_year    = _acad_yr_ue,
                                                note_ue          = round(_note_ue, 2),
                                                credits_obtained = _cred_obt,
                                                decision         = _dec_ue,
                                                computed_by      = user["id"],
                                            )
                                            _n_ue_saved += 1
                                        except Exception:
                                            pass
                                st.success(
                                    f"✅ {_n_ue_saved} résultat(s) UE enregistré(s)."
                                )
                                st.rerun()
                        else:
                            st.caption(
                                "💡 Assignez vos cours à des UE (onglet **Cours**) "
                                "pour activer les résultats par unité d'enseignement."
                            )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 10 : FILIÈRES
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[10]:
        st.markdown("#### Filières du département")
        st.caption("Une filière regroupe plusieurs options d'étude au sein d'un département.")

        try:
            filieres = FiliereQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); filieres = []

        st.metric("Filières", len(filieres))
        st.divider()

        with st.expander("➕ Ajouter une filière"):
            with st.form("add_filiere"):
                fil_name = st.text_input("Nom * (ex: Informatique)")
                fil_code = st.text_input("Code (ex: INFO)")
                fil_desc = st.text_area("Description (optionnel)")
                if st.form_submit_button("Créer", type="primary"):
                    if fil_name.strip():
                        try:
                            FiliereQueries.create(
                                fil_name.strip(), dept_id,
                                fil_code.strip(), fil_desc.strip()
                            )
                            st.success(f"✅ Filière '{fil_name.strip()}' créée !")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
                    else:
                        st.error("Nom obligatoire.")

        for fil in filieres:
            with st.expander(
                f"🔬 {fil['name']}"
                + (f" ({fil['code']})" if fil.get("code") else "")
            ):
                if fil.get("description"):
                    st.caption(fil["description"])
                with st.form(f"edit_fil_{fil['id']}"):
                    fn = st.text_input("Nom *",  value=fil["name"])
                    fc = st.text_input("Code",   value=fil.get("code") or "")
                    fd = st.text_area("Description", value=fil.get("description") or "")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            try:
                                FiliereQueries.update(fil["id"], fn, fc, fd)
                                st.success("✅ Filière mise à jour !"); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            try:
                                FiliereQueries.delete(fil["id"])
                                st.success("✅ Filière supprimée."); st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 11 : OPTIONS
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[11]:
        st.markdown("#### Options d'étude")
        st.caption("Chaque option appartient à une filière. "
                   "Ex : Filière Informatique → Option Génie Logiciel, Option Réseaux…")

        try:
            filieres_opt = FiliereQueries.get_by_department(dept_id)
            all_options  = OptionEtudeQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); filieres_opt = []; all_options = []

        if not filieres_opt:
            st.info("Créez d'abord des filières dans l'onglet **Filières**.")
        else:
            st.metric("Options", len(all_options))
            st.divider()

            with st.expander("➕ Ajouter une option"):
                with st.form("add_option"):
                    opt_fil  = st.selectbox(
                        "Filière *", options=filieres_opt,
                        format_func=lambda f: f["name"]
                    )
                    opt_name = st.text_input("Nom * (ex: Génie Logiciel)")
                    opt_code = st.text_input("Code (ex: GL)")
                    opt_desc = st.text_area("Description (optionnel)")
                    if st.form_submit_button("Créer", type="primary"):
                        if opt_name.strip() and opt_fil:
                            try:
                                OptionEtudeQueries.create(
                                    opt_name.strip(), opt_fil["id"],
                                    opt_code.strip(), opt_desc.strip()
                                )
                                st.success(f"✅ Option '{opt_name.strip()}' créée !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                        else:
                            st.error("Filière et nom obligatoires.")

            for opt in all_options:
                with st.expander(
                    f"🗂️ {opt['name']}"
                    + (f" ({opt['code']})" if opt.get("code") else "")
                    + f" — {opt.get('filiere_name','—')}"
                ):
                    with st.form(f"edit_opt_{opt['id']}"):
                        on = st.text_input("Nom *",  value=opt["name"])
                        oc = st.text_input("Code",   value=opt.get("code") or "")
                        od = st.text_area("Description", value=opt.get("description") or "")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Sauvegarder"):
                                try:
                                    OptionEtudeQueries.update(opt["id"], on, oc, od)
                                    st.success("✅ Option mise à jour !"); st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur : {e}")
                        with col2:
                            if st.form_submit_button("🗑️ Supprimer"):
                                try:
                                    OptionEtudeQueries.delete(opt["id"])
                                    st.success("✅ Option supprimée."); st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur : {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 12 : INSCRIPTIONS (fusionné dans Registre)
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[12]:
        st.info(
            "La gestion des inscriptions et des statuts académiques "
            "(Inscrit / Admis / Redoublant / Transféré / Abandonné) "
            "se fait désormais directement depuis l'onglet **Registre Étudiants**. "
            "Ouvrez la fiche d'un étudiant pour modifier son statut."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 13 : DEMANDES DE MODIFICATION DE COTES
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[13]:
        from datetime import datetime as _dt

        st.markdown("#### Demandes de modification de cotes")
        st.caption(
            "Les professeurs soumettent ici leurs demandes de modification "
            "après le délai de 48 h. Approuvez ou refusez chaque demande."
        )

        try:
            pending_reqs = GradeModificationRequestQueries.get_pending_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); pending_reqs = []

        if not pending_reqs:
            st.success("✅ Aucune demande en attente.")
        else:
            st.metric("Demandes en attente", len(pending_reqs))
            st.divider()

            for req in pending_reqs:
                _req_at = req.get("requested_at")
                _req_at_str = (
                    _req_at.strftime("%d/%m/%Y à %H:%M") if _req_at else "—"
                )
                _cur_grade = req.get("current_grade")
                _req_grade = req.get("requested_grade")
                _cur_max   = req.get("current_max")
                _req_max   = req.get("requested_max") or _cur_max

                with st.expander(
                    f"📝 {req.get('student_name','—')} · {req.get('course_name','—')} "
                    f"· {req.get('exam_type','—')} · Session {req.get('session_name','—')} "
                    f"— {_req_at_str}"
                ):
                    col_info, col_chg = st.columns(2)
                    with col_info:
                        st.markdown("**Informations**")
                        st.caption(f"Étudiant : **{req.get('student_name','—')}** "
                                   f"({req.get('student_number','—')})")
                        st.caption(f"Classe : {req.get('class_name','—')}")
                        st.caption(f"Cours : {req.get('course_name','—')}")
                        st.caption(f"Type : {req.get('exam_type','—')} · "
                                   f"Session : {req.get('session_name','—')}")
                        st.caption(f"Professeur : {req.get('professor_name','—')}")
                        st.caption(f"Demandé le : {_req_at_str}")
                    with col_chg:
                        st.markdown("**Modification demandée**")
                        _c1, _c2 = st.columns(2)
                        with _c1:
                            st.markdown("Actuel")
                            st.info(
                                f"{_cur_grade}/{_cur_max}"
                                if _cur_grade is not None else "—"
                            )
                            if req.get("current_comment"):
                                st.caption(f"Commentaire : {req['current_comment']}")
                        with _c2:
                            st.markdown("Demandé")
                            st.warning(
                                f"{_req_grade}/{_req_max}"
                                if _req_grade is not None else "—"
                            )
                            if req.get("requested_comment"):
                                st.caption(f"Commentaire : {req['requested_comment']}")

                    st.markdown(f"**Motif du professeur :** {req.get('motif','—')}")
                    st.divider()

                    with st.form(f"review_req_{req['id']}"):
                        _decision = st.radio(
                            "Décision *",
                            options=["approuver", "rejeter"],
                            format_func=lambda x: "✅ Approuver" if x == "approuver" else "❌ Rejeter",
                            horizontal=True,
                            key=f"dec_{req['id']}"
                        )
                        _admin_resp = st.text_area(
                            "Réponse / commentaire (optionnel)",
                            key=f"resp_{req['id']}"
                        )
                        if st.form_submit_button("Valider la décision", type="primary"):
                            try:
                                if _decision == "approuver":
                                    GradeModificationRequestQueries.approve(
                                        req["id"], user["id"], _admin_resp.strip() or None
                                    )
                                    st.success("✅ Modification approuvée et appliquée.")
                                else:
                                    GradeModificationRequestQueries.reject(
                                        req["id"], user["id"], _admin_resp.strip() or None
                                    )
                                    st.warning("❌ Demande rejetée.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 14 : PRÉSENCES
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[14]:
        import pandas as _pd_pres

        st.markdown("#### Suivi des présences")
        st.caption("Consultez l'assiduité des étudiants par classe et par cours.")

        try:
            _pres_promos = PromotionQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); _pres_promos = []

        if not _pres_promos:
            st.info("Aucune promotion dans ce département.")
        else:
            _pc1, _pc2 = st.columns(2)
            with _pc1:
                _pres_promo = st.selectbox(
                    "Promotion", options=_pres_promos,
                    format_func=lambda p: f"{p['name']} ({p['academic_year']})",
                    key="pres_promo"
                )
            _pres_classes = ClassQueries.get_by_promotion(_pres_promo["id"]) if _pres_promo else []
            with _pc2:
                _pres_class = st.selectbox(
                    "Salle / Classe", options=_pres_classes,
                    format_func=lambda c: c["name"],
                    key="pres_class"
                ) if _pres_classes else None

            if _pres_class:
                try:
                    _absences = AttendanceQueries.get_absences_by_class(_pres_class["id"])
                    _detail   = AttendanceQueries.get_stats_by_class(_pres_class["id"])
                except Exception as e:
                    st.error(f"Erreur : {e}"); _absences = []; _detail = []

                if not _absences:
                    st.info("Aucune donnée de présence enregistrée pour cette classe.")
                else:
                    # ── Résumé global ──────────────────────────────────────────
                    _total_absences = sum(r["absences"] for r in _absences)
                    _total_seances  = sum(r["total_seances"] for r in _absences)
                    _taux_global    = (
                        round(sum(r["presences"] for r in _absences)
                              / _total_seances * 100, 1)
                        if _total_seances else 0
                    )
                    _ma1, _ma2, _ma3 = st.columns(3)
                    _ma1.metric("Séances enregistrées", _total_seances)
                    _ma2.metric("Absences (non justifiées)", _total_absences)
                    _ma3.metric("Taux de présence moyen", f"{_taux_global} %")
                    st.divider()

                    # ── Vue "Alertes" : étudiants avec beaucoup d'absences ─────
                    _seuil = st.slider("Seuil d'alerte (absences)", 1, 20, 3,
                                       key="pres_seuil")
                    _alertes = [r for r in _absences if (r["absences"] or 0) >= _seuil]
                    if _alertes:
                        st.markdown(f"##### ⚠️ Étudiants avec ≥ {_seuil} absence(s)")
                        for _a in _alertes:
                            st.error(
                                f"**{_a['student_name']}** ({_a['student_number']}) — "
                                f"{_a['absences']} absence(s) / {_a['total_seances']} séance(s)"
                            )
                    else:
                        st.success(f"✅ Aucun étudiant n'a atteint le seuil de {_seuil} absence(s).")

                    st.divider()

                    # ── Tableau complet ────────────────────────────────────────
                    st.markdown("##### Tableau récapitulatif")
                    _view = st.radio(
                        "Vue", ["Par étudiant", "Par cours"],
                        horizontal=True, key="pres_view"
                    )

                    if _view == "Par étudiant":
                        _df_pres = _pd_pres.DataFrame([{
                            "Étudiant":      r["student_name"],
                            "N°":            r["student_number"],
                            "Séances":       r["total_seances"],
                            "Présences":     r["presences"],
                            "Absences":      r["absences"],
                            "Justifiées":    r["justifies"],
                            "Taux (%)":      float(r["taux_presence"] or 0),
                        } for r in _absences])
                        st.dataframe(
                            _df_pres.sort_values("Taux (%)", ascending=True),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        # Agréger par cours
                        _by_course = {}
                        for row in _detail:
                            cn = row["course_name"]
                            if cn not in _by_course:
                                _by_course[cn] = {"Cours": cn, "Séances": 0,
                                                   "Présences": 0, "Absences": 0,
                                                   "Justifiées": 0}
                            _by_course[cn]["Séances"]    += (row["total_seances"] or 0)
                            _by_course[cn]["Présences"]  += (row["presences"] or 0)
                            _by_course[cn]["Absences"]   += (row["absences"] or 0)
                            _by_course[cn]["Justifiées"] += (row["justifies"] or 0)
                        for cn in _by_course:
                            s = _by_course[cn]["Séances"]
                            p = _by_course[cn]["Présences"]
                            _by_course[cn]["Taux (%)"] = round(p / s * 100, 1) if s else 0.0
                        _df_cours = _pd_pres.DataFrame(list(_by_course.values()))
                        st.dataframe(
                            _df_cours.sort_values("Taux (%)", ascending=True),
                            use_container_width=True, hide_index=True
                        )

                    # ── Export ────────────────────────────────────────────────
                    import io as _io_pres
                    _buf_pres = _io_pres.BytesIO()
                    _pd_pres.DataFrame([{
                        "Étudiant":   r["student_name"],
                        "N°":         r["student_number"],
                        "Séances":    r["total_seances"],
                        "Présences":  r["presences"],
                        "Absences":   r["absences"],
                        "Justifiées": r["justifies"],
                        "Taux (%)":   float(r["taux_presence"] or 0),
                    } for r in _absences]).to_excel(
                        _buf_pres, index=False, engine="openpyxl"
                    )
                    st.download_button(
                        "📥 Exporter Excel",
                        data=_buf_pres.getvalue(),
                        file_name=f"presences_{_pres_class['name'].replace(' ','_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 15 : RÉCLAMATIONS DE NOTES
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[15]:
        st.markdown("#### Réclamations de notes")
        st.caption(
            "Réclamations déposées par les étudiants et en attente de traitement "
            "par les professeurs concernés."
        )

        try:
            _claims = GradeClaimQueries.get_pending_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); _claims = []

        if not _claims:
            st.success("✅ Aucune réclamation en attente dans ce département.")
        else:
            st.metric("Réclamations en attente", len(_claims))
            st.divider()

            for _cl in _claims:
                _cl_at = _cl.get("created_at")
                _cl_at_str = _cl_at.strftime("%d/%m/%Y à %H:%M") if _cl_at else "—"
                _grade_val = _cl.get("grade")
                _max_val   = _cl.get("max_grade")

                with st.expander(
                    f"📩 {_cl.get('student_name','—')} · {_cl.get('course_name','—')} "
                    f"· {_cl.get('exam_type','—')} — {_cl_at_str}"
                ):
                    _ci1, _ci2 = st.columns(2)
                    with _ci1:
                        st.markdown("**Étudiant**")
                        st.caption(
                            f"{_cl.get('student_name','—')} "
                            f"({_cl.get('student_number','—')})"
                        )
                        st.caption(f"Classe : {_cl.get('class_name','—')}")
                        st.caption(f"Déposée le : {_cl_at_str}")
                    with _ci2:
                        st.markdown("**Note contestée**")
                        st.caption(
                            f"Cours : {_cl.get('course_name','—')} · "
                            f"{_cl.get('exam_type','—')} · "
                            f"Session : {_cl.get('session_name','—')}"
                        )
                        if _grade_val is not None:
                            st.info(f"Note : **{_grade_val}/{_max_val}**")
                        st.caption(f"Professeur : {_cl.get('professor_name','—')}")

                    st.markdown(f"**Motif de la réclamation :** {_cl.get('reason','—')}")
                    st.caption(
                        "ℹ️ La réponse finale est donnée par le professeur concerné. "
                        "Cette vue vous permet de superviser les réclamations ouvertes."
                    )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 16 : BULLETINS
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[16]:
        from db.queries import (BulletinQueries as _BQTAB,
                                StudentResultsQueries as _SRQTAB,
                                ClassQueries as _CQT16,
                                PromotionQueries as _PQT16)
        import pandas as _pd16

        st.markdown("#### Bulletins du département")
        st.caption(
            "Vue d'ensemble de tous les bulletins de session — statuts, "
            "décisions et accès rapide aux résultats calculés."
        )

        try:
            _buls = _BQTAB.get_by_department(dept_id)
        except Exception as _eb:
            st.error(f"Erreur : {_eb}"); _buls = []

        if not _buls:
            st.info(
                "Aucun bulletin trouvé. Allez dans l'onglet **Résultats**, "
                "validez des notes et les bulletins apparaîtront ici."
            )
        else:
            _B_CLR = {"brouillon": "#64748B", "valide": "#10B981", "publie": "#6D28D9"}
            _B_LBL = {"brouillon": "Brouillon", "valide": "Validé", "publie": "Publié"}

            _nb_bro = sum(1 for b in _buls if b.get("status") == "brouillon")
            _nb_val = sum(1 for b in _buls if b.get("status") == "valide")
            _nb_pub = sum(1 for b in _buls if b.get("status") == "publie")
            _m1, _m2, _m3, _m4 = st.columns(4)
            _m1.metric("Total bulletins", len(_buls))
            _m2.metric("Brouillon", _nb_bro)
            _m3.metric("Validé", _nb_val)
            _m4.metric("Publié", _nb_pub)
            st.divider()

            # Filtres
            _filt_col1, _filt_col2 = st.columns(2)
            _all_sessions_bul = sorted(set(b.get("session_name","") for b in _buls))
            _all_statuses_bul = ["Tous", "brouillon", "valide", "publie"]
            _sel_session_bul = _filt_col1.selectbox(
                "Session", ["Toutes"] + _all_sessions_bul, key="bul_session_filter"
            )
            _sel_status_bul = _filt_col2.selectbox(
                "Statut", _all_statuses_bul, key="bul_status_filter"
            )

            _buls_f = [
                b for b in _buls
                if (_sel_session_bul == "Toutes" or b.get("session_name") == _sel_session_bul)
                and (_sel_status_bul == "Tous" or b.get("status") == _sel_status_bul)
            ]

            for _bul in _buls_f:
                _b_st   = _bul.get("status","brouillon")
                _b_clr  = _B_CLR.get(_b_st, "#64748B")
                _b_lbl  = _B_LBL.get(_b_st, _b_st)
                _b_pub  = _bul.get("published_at")
                _b_pub_str = _b_pub.strftime("%d/%m/%Y") if _b_pub else "—"

                with st.expander(
                    f"📋 {_bul.get('class_name','—')}  ·  "
                    f"{_bul.get('session_name','—')}  ·  "
                    f"{_bul.get('academic_year','—')}  —  "
                    f"{_b_lbl}"
                ):
                    _bc1, _bc2 = st.columns(2)
                    with _bc1:
                        st.markdown(
                            f"<span style='background:{_b_clr}20;color:{_b_clr};"
                            f"padding:2px 10px;border-radius:20px;font-size:0.8rem;"
                            f"font-weight:600'>{_b_lbl}</span>",
                            unsafe_allow_html=True
                        )
                        st.caption(f"Promotion : {_bul.get('promotion_name','—')}")
                        st.caption(f"Classe : {_bul.get('class_name','—')}")
                        st.caption(f"Publication : {_b_pub_str}")
                    with _bc2:
                        # Résultats calculés pour ce bulletin
                        try:
                            _bul_results = _SRQTAB.get_by_class_session(
                                _bul["class_id"], _bul["session_name"]
                            )
                        except Exception:
                            _bul_results = []

                        if _bul_results:
                            _nb_a  = sum(1 for r in _bul_results if r.get("decision") == "Admis")
                            _nb_s2 = sum(1 for r in _bul_results if r.get("decision") == "Session 2")
                            _nb_aj = sum(1 for r in _bul_results if r.get("decision") == "Ajourné")
                            _nb_tot = len(_bul_results)
                            st.markdown(
                                f"**{_nb_tot}** étudiants · "
                                f"<span style='color:#059669'>✅ {_nb_a} Admis</span> · "
                                f"<span style='color:#D97706'>⚠️ {_nb_s2} Sess.2</span> · "
                                f"<span style='color:#EF4444'>❌ {_nb_aj} Ajournés</span>",
                                unsafe_allow_html=True
                            )
                            # Mini-tableau
                            _df_bul = _pd16.DataFrame([
                                {
                                    "Rang":    r.get("rank","—"),
                                    "Étudiant":r.get("student_name","—"),
                                    "N°":      r.get("student_number","—"),
                                    "Moyenne": f"{float(r['average']):.2f}/20" if r.get("average") is not None else "—",
                                    "Décision":r.get("decision","—"),
                                }
                                for r in _bul_results
                            ])
                            st.dataframe(_df_bul, use_container_width=True,
                                         hide_index=True)
                        else:
                            st.caption(
                                "Aucune décision calculée — utilisez le bouton "
                                "🧮 dans l'onglet Résultats."
                            )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 17 : ANNÉES ACADÉMIQUES
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[17]:
        from db.queries import AcademicYearQueries as _AYQ

        _ay_uni_id = (dept.get("university_id") if dept else None) or user.get("university_id")

        st.markdown("#### Années académiques")
        st.caption(
            "Gérez les années académiques de votre université. "
            "L'année marquée **Courante** sert de référence par défaut "
            "pour les promotions, inscriptions et bulletins."
        )

        if not _ay_uni_id:
            st.warning("Impossible de déterminer l'université associée.")
        else:
            try:
                _ay_list = _AYQ.get_by_university(_ay_uni_id) or []
            except Exception as _e:
                st.error(f"Erreur : {_e}"); _ay_list = []

            _ay_current = next((a for a in _ay_list if a.get("is_current")), None)

            # ── Métriques ─────────────────────────────────────────────────────
            _m1, _m2, _m3 = st.columns(3)
            _m1.metric("Années enregistrées", len(_ay_list))
            _m2.metric("Année courante", _ay_current["label"] if _ay_current else "—")
            _m3.metric(
                "Actives",
                sum(1 for a in _ay_list if a.get("status") == "active")
            )
            st.divider()

            # ── Créer une nouvelle année ──────────────────────────────────────
            with st.expander("➕ Créer une nouvelle année académique"):
                with st.form("form_create_ay"):
                    _ay_c1, _ay_c2 = st.columns(2)
                    _new_label = _ay_c1.text_input(
                        "Label * (ex: 2025-2026)",
                        placeholder="2025-2026",
                        key="ay_new_label"
                    )
                    _new_status = _ay_c2.selectbox(
                        "Statut",
                        ["planned", "active", "archived"],
                        index=1,
                        key="ay_new_status"
                    )
                    _ay_d1, _ay_d2 = st.columns(2)
                    _new_start = _ay_d1.date_input(
                        "Date de début", value=None, key="ay_new_start"
                    )
                    _new_end = _ay_d2.date_input(
                        "Date de fin", value=None, key="ay_new_end"
                    )
                    _new_notes = st.text_area(
                        "Remarques (optionnel)", key="ay_new_notes"
                    )
                    _set_current_new = st.checkbox(
                        "Définir comme année courante", key="ay_set_current_new"
                    )

                    if st.form_submit_button("✅ Créer", type="primary"):
                        _lbl = _new_label.strip()
                        if not _lbl:
                            st.error("Le label est obligatoire (ex: 2025-2026).")
                        else:
                            import re as _re
                            if not _re.match(r"^\d{4}-\d{4}$", _lbl):
                                st.error(
                                    "Format attendu : AAAA-AAAA "
                                    "(ex: 2025-2026)."
                                )
                            else:
                                try:
                                    _res = _AYQ.create(
                                        university_id=_ay_uni_id,
                                        label=_lbl,
                                        start_date=_new_start,
                                        end_date=_new_end,
                                        notes=_new_notes.strip() or None,
                                        status=_new_status,
                                    )
                                    if _set_current_new and _res:
                                        _AYQ.set_current(_res["id"], _ay_uni_id)
                                    st.success(f"✅ Année '{_lbl}' créée !")
                                    st.rerun()
                                except Exception as _ec:
                                    st.error(f"Erreur : {_ec}")

            # ── Liste des années ──────────────────────────────────────────────
            _ST_CLR = {
                "active":   ("#059669", "#D1FAE5"),
                "planned":  ("#D97706", "#FEF3C7"),
                "archived": ("#64748B", "#F1F5F9"),
            }
            _ST_LBL = {
                "active":   "Active",
                "planned":  "Planifiée",
                "archived": "Archivée",
            }

            if not _ay_list:
                st.info(
                    "Aucune année académique enregistrée. "
                    "Créez-en une ci-dessus."
                )
            else:
                for _ay in _ay_list:
                    _is_cur   = bool(_ay.get("is_current"))
                    _ay_st    = _ay.get("status", "active")
                    _clr, _bg = _ST_CLR.get(_ay_st, ("#64748B", "#F1F5F9"))
                    _lbl_st   = _ST_LBL.get(_ay_st, _ay_st)
                    _cur_tag  = " ⭐ Courante" if _is_cur else ""
                    _sd  = (_ay.get("start_date").strftime("%d/%m/%Y")
                            if _ay.get("start_date") else "—")
                    _ed  = (_ay.get("end_date").strftime("%d/%m/%Y")
                            if _ay.get("end_date") else "—")

                    with st.expander(
                        f"🗓️ {_ay['label']}{_cur_tag}  ·  {_lbl_st}"
                    ):
                        _ac1, _ac2 = st.columns([3, 1])
                        with _ac1:
                            st.markdown(
                                f"<span style='background:{_bg};color:{_clr};"
                                f"padding:2px 10px;border-radius:20px;"
                                f"font-size:0.8rem;font-weight:600'>"
                                f"{_lbl_st}</span>"
                                + (
                                    "  <span style='background:#FEF3C7;color:#D97706;"
                                    "padding:2px 10px;border-radius:20px;"
                                    "font-size:0.8rem;font-weight:600'>⭐ Courante</span>"
                                    if _is_cur else ""
                                ),
                                unsafe_allow_html=True
                            )
                            st.caption(f"Période : {_sd} → {_ed}")
                            if _ay.get("notes"):
                                st.caption(f"Remarques : {_ay['notes']}")

                        with _ac2:
                            if not _is_cur:
                                if st.button(
                                    "⭐ Définir comme courante",
                                    key=f"ay_set_{_ay['id']}",
                                    use_container_width=True,
                                ):
                                    try:
                                        _AYQ.set_current(_ay["id"], _ay_uni_id)
                                        st.success(
                                            f"✅ '{_ay['label']}' est "
                                            f"maintenant l'année courante."
                                        )
                                        st.rerun()
                                    except Exception as _es:
                                        st.error(f"Erreur : {_es}")

                            if _ay_st != "archived":
                                if st.button(
                                    "📦 Archiver",
                                    key=f"ay_arch_{_ay['id']}",
                                    use_container_width=True,
                                ):
                                    try:
                                        _AYQ.set_status(_ay["id"], "archived")
                                        st.success(
                                            f"'{_ay['label']}' archivée."
                                        )
                                        st.rerun()
                                    except Exception as _ea:
                                        st.error(f"Erreur : {_ea}")
                            else:
                                if st.button(
                                    "♻️ Réactiver",
                                    key=f"ay_react_{_ay['id']}",
                                    use_container_width=True,
                                ):
                                    try:
                                        _AYQ.set_status(_ay["id"], "active")
                                        st.success(
                                            f"'{_ay['label']}' réactivée."
                                        )
                                        st.rerun()
                                    except Exception as _er:
                                        st.error(f"Erreur : {_er}")


    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 18 : ANALYSES (anomalies, at-risk, top étudiants)
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[18]:
        from db.queries import (AnalyticsQueries as _AnaQ,
                                PromotionQueries  as _PQA,
                                ClassQueries      as _CQA,
                                GradeQueries      as _GQA)
        import pandas as _pdA

        st.markdown("#### Analyses & Intelligence")
        st.caption(
            "Détection d'anomalies dans les notes, étudiants à risque, "
            "classements et performance par cours."
        )

        # ── Sélecteurs ────────────────────────────────────────────────────────
        try:
            _promos_a = _PQA.get_by_department(dept_id) or []
        except Exception:
            _promos_a = []

        if not _promos_a:
            st.info("Aucune promotion disponible.")
        else:
            _ac1, _ac2, _ac3 = st.columns(3)
            _promo_a = _ac1.selectbox(
                "Promotion",
                options=_promos_a,
                format_func=lambda p: f"{p['name']} ({p['academic_year']})",
                key="ana_promo"
            )
            _classes_a = _CQA.get_by_promotion(_promo_a["id"]) if _promo_a else []
            _class_a = _ac2.selectbox(
                "Classe",
                options=_classes_a,
                format_func=lambda c: c["name"],
                key="ana_class"
            ) if _classes_a else None

            _sessions_a = []
            if _class_a:
                try:
                    _sessions_a = [
                        s["session_name"]
                        for s in (_GQA.get_sessions_by_class(_class_a["id"]) or [])
                    ]
                except Exception:
                    pass
            _session_a = _ac3.selectbox(
                "Session", options=_sessions_a, key="ana_session"
            ) if _sessions_a else None

            if not _class_a or not _session_a:
                st.info("Sélectionnez une classe et une session pour afficher les analyses.")
            else:
                st.divider()

                # ── 1. Décisions (si calculées) ───────────────────────────────
                try:
                    _dec_summ = _AnaQ.get_session_decision_summary(
                        _class_a["id"], _session_a
                    ) or []
                except Exception:
                    _dec_summ = []

                if _dec_summ:
                    st.markdown("##### Répartition des décisions")
                    _dm = {r["decision"]: r for r in _dec_summ}
                    _total_dec = sum(int(r["cnt"]) for r in _dec_summ)
                    _dcols = st.columns(3)
                    _DEC_C = {
                        "Admis":     ("#059669", "#D1FAE5"),
                        "Session 2": ("#D97706", "#FEF3C7"),
                        "Ajourné":   ("#DC2626", "#FEE2E2"),
                    }
                    for _i, _dec_key in enumerate(["Admis", "Session 2", "Ajourné"]):
                        _row = _dm.get(_dec_key)
                        _cnt = int(_row["cnt"]) if _row else 0
                        _avg_d = float(_row["avg_decision"]) if _row and _row.get("avg_decision") else 0
                        _pct = round(_cnt / _total_dec * 100, 1) if _total_dec else 0
                        _clr, _bg = _DEC_C[_dec_key]
                        _dcols[_i].markdown(
                            f"<div style='padding:1rem;background:{_bg};"
                            f"border:1px solid {_clr}44;border-radius:10px;"
                            f"text-align:center'>"
                            f"<div style='font-size:0.8rem;color:{_clr};"
                            f"font-weight:600'>{_dec_key}</div>"
                            f"<div style='font-size:2rem;font-weight:800;"
                            f"color:{_clr}'>{_cnt}</div>"
                            f"<div style='font-size:0.75rem;color:#64748B'>"
                            f"{_pct}% · moy. {_avg_d:.2f}/20</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    st.markdown("")
                else:
                    st.info(
                        "Aucune décision calculée pour cette session. "
                        "Utilisez **🧮 Calculer les décisions** dans l'onglet Résultats."
                    )

                st.divider()

                # ── 2. Performance par cours + anomalies ──────────────────────
                st.markdown("##### Performance par cours")
                try:
                    _cp = _AnaQ.get_course_performance(
                        _class_a["id"], _session_a
                    ) or []
                except Exception as _e:
                    st.error(f"Erreur : {_e}"); _cp = []

                if _cp:
                    _ANOM_RULES = [
                        (lambda r: float(r["avg_20"] or 0) > 17,
                         "Moyenne très élevée (>17/20)"),
                        (lambda r: float(r["avg_20"] or 0) < 5,
                         "Moyenne très basse (<5/20)"),
                        (lambda r: r.get("std_dev") is not None
                         and float(r["std_dev"] or 0) < 0.5
                         and int(r["nb_students"]) > 2,
                         "Distribution suspecte (écart-type < 0.5)"),
                        (lambda r: r.get("std_dev") is not None
                         and float(r["std_dev"] or 0) > 7,
                         "Distribution très dispersée (écart-type > 7)"),
                    ]

                    _anomalies = []
                    _cp_rows = []
                    for _r in _cp:
                        _flags = [msg for fn, msg in _ANOM_RULES if fn(_r)]
                        _anomalies.extend(
                            {"course": _r["course_name"],
                             "professor": _r["professor_name"],
                             "flag": f} for f in _flags
                        )
                        _cp_rows.append({
                            "Cours":      _r["course_name"],
                            "Professeur": _r["professor_name"],
                            "Étudiants":  _r["nb_students"],
                            "Moy./20":    float(_r["avg_20"] or 0),
                            "Min/20":     float(_r["min_20"] or 0),
                            "Max/20":     float(_r["max_20"] or 0),
                            "Écart-type": float(_r["std_dev"] or 0) if _r.get("std_dev") else "—",
                            "⚠️":         "⚠️" if _flags else "✅",
                        })

                    _df_cp = _pdA.DataFrame(_cp_rows)
                    st.dataframe(_df_cp, use_container_width=True, hide_index=True)

                    # Alertes d'anomalies
                    if _anomalies:
                        st.markdown("##### ⚠️ Anomalies détectées")
                        for _an in _anomalies:
                            st.warning(
                                f"**{_an['course']}** "
                                f"(Prof : {_an['professor']}) — "
                                f"{_an['flag']}"
                            )
                    else:
                        st.success("✅ Aucune anomalie détectée dans les distributions.")
                else:
                    st.info("Aucune note disponible pour cette session.")

                st.divider()

                # ── 3. Étudiants à risque ────────────────────────────────────
                st.markdown("##### Étudiants à risque")
                try:
                    _at_risk = _AnaQ.get_at_risk_students(
                        _class_a["id"], _session_a
                    ) or []
                except Exception:
                    _at_risk = []

                if not _at_risk:
                    st.success(
                        "✅ Aucun étudiant à risque identifié "
                        "(ou décisions non encore calculées)."
                    )
                else:
                    _nb_sess2  = sum(1 for r in _at_risk if r["decision"] == "Session 2")
                    _nb_ajourn = sum(1 for r in _at_risk if r["decision"] == "Ajourné")
                    st.markdown(
                        f"**{len(_at_risk)} étudiant(s)** en difficulté — "
                        f"Session 2 : {_nb_sess2} · Ajournés : {_nb_ajourn}"
                    )

                    _risk_rows = []
                    for _rr in _at_risk:
                        _risk_rows.append({
                            "Rang":     _rr.get("rank", "—"),
                            "Étudiant": _rr["student_name"],
                            "N°":       _rr["student_number"],
                            "Moy./20":  float(_rr["average"]) if _rr.get("average") else "—",
                            "Décision": _rr["decision"],
                            "Email":    _rr.get("email") or "—",
                        })
                    st.dataframe(
                        _pdA.DataFrame(_risk_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Bouton de notification
                    _with_email = [r for r in _at_risk if r.get("email")]
                    if _with_email:
                        if st.button(
                            f"📧 Notifier {len(_with_email)} étudiant(s) à risque",
                            key="btn_notify_risk",
                            type="primary",
                        ):
                            try:
                                from utils.notifications import notify_at_risk as _nar
                                _sent_r = _nar(
                                    student_data=_at_risk,
                                    session_name=_session_a,
                                    university=(
                                        dept.get("university_name", "UniSchedule")
                                        if dept else "UniSchedule"
                                    ),
                                )
                                st.success(
                                    f"📧 {_sent_r} notification(s) envoyée(s)."
                                )
                            except Exception as _en:
                                st.error(f"Erreur envoi : {_en}")
                    else:
                        st.caption("Aucun email enregistré pour ces étudiants.")

                st.divider()

                # ── 4. Top étudiants ─────────────────────────────────────────
                st.markdown("##### Top étudiants (Admis)")
                try:
                    _top = _AnaQ.get_top_students(
                        _class_a["id"], _session_a, limit=10
                    ) or []
                except Exception:
                    _top = []

                if not _top:
                    st.info(
                        "Aucun étudiant admis identifié "
                        "(ou décisions non encore calculées)."
                    )
                else:
                    _MEDALS = ["🥇", "🥈", "🥉"]
                    for _ti, _tr in enumerate(_top):
                        _medal = _MEDALS[_ti] if _ti < 3 else f"{_ti+1}."
                        _avg_t = float(_tr["average"]) if _tr.get("average") else 0
                        _bar_w = int(_avg_t / 20 * 100)
                        st.markdown(
                            f"<div style='display:flex;align-items:center;"
                            f"gap:0.75rem;margin-bottom:0.5rem'>"
                            f"<span style='font-size:1.25rem;min-width:2rem'>{_medal}</span>"
                            f"<div style='flex:1'>"
                            f"<div style='display:flex;justify-content:space-between'>"
                            f"<span style='font-weight:600;color:#1E293B'>"
                            f"{_tr['student_name']}</span>"
                            f"<span style='font-weight:700;color:#059669'>"
                            f"{_avg_t:.2f}/20</span>"
                            f"</div>"
                            f"<div style='background:#E2E8F0;border-radius:4px;"
                            f"height:6px;margin-top:4px'>"
                            f"<div style='background:#059669;width:{_bar_w}%;"
                            f"height:6px;border-radius:4px'></div>"
                            f"</div>"
                            f"</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )


# ══════════════════════════════════════════════════════════════════════════════
# ROUTING — après la définition de toutes les fonctions
# ══════════════════════════════════════════════════════════════════════════════
if role == "super_admin":
    render_super_admin()
elif role == "admin_universite":
    render_admin_universite()
elif role == "admin_faculte":
    render_admin_faculte()
elif role == "admin_departement":
    render_admin_departement()
elif role == "professeur":
    st.switch_page("pages/9_Prof_Dashboard.py")
else:
    st.error("Rôle non reconnu.")
