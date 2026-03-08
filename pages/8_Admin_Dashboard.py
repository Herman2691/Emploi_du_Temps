# pages/8_Admin_Dashboard.py
import streamlit as st
from utils.auth import require_auth, get_current_user, ROLE_LABELS, create_admin
from utils.components import inject_global_css, page_header, role_badge, announcement_card, render_schedule_table

inject_global_css()
require_auth()

user = get_current_user()
role = user["role"]

# ── En-tête ───────────────────────────────────────────────────────────────────
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

    tab_unis, tab_admins = st.tabs(["🏛️ Universités", "👥 Comptes Administrateurs"])

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
                photo   = st.text_input("URL Photo (optionnel)")
                website = st.text_input("Site web (optionnel)")
                if st.form_submit_button("Créer", type="primary"):
                    if not name.strip():
                        st.error("Le nom est obligatoire.")
                    else:
                        try:
                            UniversityQueries.create(name.strip(), address, photo, website)
                            st.success(f"✅ Université '{name.strip()}' créée !"); st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

        # ── Universités actives ───────────────────────────────────────────────
        if active_unis:
            st.markdown("#### ✅ Universités actives")
            for uni in active_unis:
                with st.expander(f"🏛️ {uni['name']}"):
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

                    # Modifier
                    st.markdown("**✏️ Modifier**")
                    with st.form(f"edit_uni_{uni['id']}"):
                        nn = st.text_input("Nom *",      value=uni["name"])
                        na = st.text_input("Adresse",    value=uni.get("address", ""))
                        np = st.text_input("Photo URL",  value=uni.get("photo_url", ""))
                        nw = st.text_input("Site web",   value=uni.get("website", ""))
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Sauvegarder", type="primary"):
                                if not nn.strip():
                                    st.error("Le nom est obligatoire.")
                                else:
                                    try:
                                        UniversityQueries.update(uni["id"], nn, na, np, nw)
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
                        st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
                        if ok: st.rerun()
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


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN UNIVERSITÉ
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_universite():
    from db.queries import FacultyQueries, UniversityQueries

    uni_id = user["university_id"]
    if not uni_id:
        st.error("Aucune université associée à ce compte."); return

    try:
        uni = UniversityQueries.get_by_id(uni_id)
    except Exception as e:
        st.error(f"Erreur : {e}"); return

    st.subheader(f"🏛️ {uni['name'] if uni else 'Votre université'}")
    tab_fac, tab_admins = st.tabs(["📚 Facultés", "👥 Admins Faculté"])

    with tab_fac:
        try:
            faculties = FacultyQueries.get_by_university(uni_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        st.metric("Facultés", len(faculties))
        st.divider()

        with st.expander("➕ Ajouter une faculté"):
            with st.form("add_fac"):
                name = st.text_input("Nom *")
                desc = st.text_area("Description")
                if st.form_submit_button("Créer", type="primary"):
                    if not name.strip():
                        st.error("Nom obligatoire.")
                    else:
                        FacultyQueries.create(name.strip(), uni_id, desc)
                        st.success("✅ Faculté créée !"); st.rerun()

        for fac in faculties:
            with st.expander(f"📗 {fac['name']}"):
                with st.form(f"edit_fac_{fac['id']}"):
                    nn = st.text_input("Nom",         value=fac["name"])
                    nd = st.text_area("Description",  value=fac.get("description",""))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            FacultyQueries.update(fac["id"],nn,nd)
                            st.success("✅"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            FacultyQueries.delete(fac["id"]); st.rerun()

    with tab_admins:
        try:
            faculties = FacultyQueries.get_by_university(uni_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        if not faculties:
            st.info("Créez d'abord des facultés.")
        else:
            with st.form("create_admin_fac"):
                name     = st.text_input("Nom complet *")
                email    = st.text_input("Email *")
                password = st.text_input("Mot de passe *", type="password")
                fac_c    = st.selectbox("Faculté *", options=faculties,
                                        format_func=lambda f: f["name"])
                if st.form_submit_button("Créer l'admin", type="primary"):
                    ok, msg = create_admin(name=name, email=email, password=password,
                                           role="admin_faculte",
                                           university_id=uni_id,
                                           faculty_id=fac_c["id"])
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")


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
                            DepartmentQueries.update(dept["id"],nn,nd)
                            st.success("✅"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            DepartmentQueries.delete(dept["id"]); st.rerun()

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
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DÉPARTEMENT
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_departement():
    from db.queries import (PromotionQueries, ClassQueries, CourseQueries,
                             ProfessorQueries, ScheduleQueries,
                             AnnouncementQueries, DepartmentQueries)

    dept_id = user["department_id"]
    if not dept_id:
        st.error("Aucun département associé à ce compte."); return

    try:
        dept = DepartmentQueries.get_by_id(dept_id)
    except Exception as e:
        st.error(f"Erreur : {e}"); return

    st.subheader(f"🏢 {dept['name'] if dept else 'Votre département'}")

    tabs = st.tabs(["🎓 Promotions", "🏫 Classes", "📘 Cours",
                    "👨‍🏫 Professeurs", "📅 Emploi du Temps", "📢 Communiqués"])

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
                year = st.text_input("Année académique *", value="2024-2025")
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
                            PromotionQueries.update(promo["id"],nn,ny)
                            st.success("✅"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            PromotionQueries.delete(promo["id"]); st.rerun()

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

                st.metric("Classes", len(classes))
                st.divider()

                with st.expander("➕ Ajouter une classe"):
                    with st.form("add_class"):
                        name     = st.text_input("Nom (ex: L1 A) *")
                        capacity = st.number_input("Capacité", min_value=1, max_value=200, value=30)
                        if st.form_submit_button("Créer", type="primary"):
                            if name.strip():
                                ClassQueries.create(name.strip(), promo_sel["id"], int(capacity))
                                st.success("✅ Classe créée !"); st.rerun()
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
                                    ClassQueries.update(cls["id"],nn,int(nc))
                                    st.success("✅"); st.rerun()
                            with col2:
                                if st.form_submit_button("🗑️ Supprimer"):
                                    ClassQueries.delete(cls["id"]); st.rerun()

    # ── COURS ─────────────────────────────────────────────────────────────────
    with tabs[2]:
        try:
            courses = CourseQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        total_h = sum(c.get("hours",0) for c in courses)
        c1, c2 = st.columns(2)
        c1.metric("Cours", len(courses))
        c2.metric("Volume horaire total", f"{total_h}h")
        st.divider()

        with st.expander("➕ Ajouter un cours"):
            with st.form("add_course"):
                name   = st.text_input("Intitulé *")
                code   = st.text_input("Code (ex: INF301)")
                hours  = st.number_input("Heures", min_value=0, max_value=500, value=30)
                weight = st.number_input("Coefficient", min_value=0.5, max_value=10.0,
                                         value=1.0, step=0.5)
                if st.form_submit_button("Créer", type="primary"):
                    if name.strip():
                        CourseQueries.create(name.strip(), code.strip(),
                                             int(hours), float(weight), dept_id)
                        st.success("✅ Cours créé !"); st.rerun()
                    else:
                        st.error("Intitulé obligatoire.")

        for course in courses:
            with st.expander(f"📘 {course['name']} ({course.get('code','—')})"):
                with st.form(f"edit_course_{course['id']}"):
                    nn = st.text_input("Intitulé",   value=course["name"])
                    nc = st.text_input("Code",        value=course.get("code",""))
                    nh = st.number_input("Heures",    value=course.get("hours",0), min_value=0)
                    nw = st.number_input("Coefficient", value=float(course.get("weight",1.0)),
                                         min_value=0.5, step=0.5)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            CourseQueries.update(course["id"],nn,nc,int(nh),float(nw))
                            st.success("✅"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            CourseQueries.delete(course["id"]); st.rerun()

    # ── PROFESSEURS ───────────────────────────────────────────────────────────
    with tabs[3]:
        try:
            professors = ProfessorQueries.get_by_department(dept_id)
        except Exception as e:
            st.error(f"Erreur : {e}"); return

        st.metric("Professeurs", len(professors))
        st.divider()

        with st.expander("➕ Ajouter un professeur"):
            with st.form("add_prof"):
                name  = st.text_input("Nom complet *")
                email = st.text_input("Email")
                phone = st.text_input("Téléphone")
                if st.form_submit_button("Ajouter", type="primary"):
                    if name.strip():
                        ProfessorQueries.create(name.strip(), email.strip(),
                                                phone.strip(), dept_id)
                        st.success("✅ Professeur ajouté !"); st.rerun()
                    else:
                        st.error("Nom obligatoire.")

        for prof in professors:
            with st.expander(f"👨‍🏫 {prof['name']}"):
                with st.form(f"edit_prof_{prof['id']}"):
                    nn = st.text_input("Nom",        value=prof["name"])
                    ne = st.text_input("Email",      value=prof.get("email",""))
                    nph= st.text_input("Téléphone",  value=prof.get("phone",""))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Sauvegarder"):
                            ProfessorQueries.update(prof["id"],nn,ne,nph)
                            st.success("✅"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Supprimer"):
                            ProfessorQueries.delete(prof["id"]); st.rerun()

    # ── EMPLOI DU TEMPS ───────────────────────────────────────────────────────
    with tabs[4]:
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
                    st.info("Aucune classe dans cette promotion.")
                else:
                    cls_sel = st.selectbox("Classe", options=classes,
                                           format_func=lambda c: c["name"],
                                           key="sched_class")
                    if cls_sel:
                        try:
                            schedules  = ScheduleQueries.get_by_class(cls_sel["id"])
                            courses    = CourseQueries.get_by_department(dept_id)
                            professors = ProfessorQueries.get_by_department(dept_id)
                        except Exception as e:
                            st.error(f"Erreur : {e}"); return

                        st.markdown("#### Grille actuelle")
                        render_schedule_table(schedules)
                        st.divider()

                        with st.expander("➕ Ajouter un créneau"):
                            if not courses:
                                st.info("Créez d'abord des cours.")
                            elif not professors:
                                st.info("Ajoutez d'abord des professeurs.")
                            else:
                                DAYS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"]
                                with st.form("add_schedule"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        day        = st.selectbox("Jour *", DAYS)
                                        start_time = st.time_input("Heure début *")
                                        end_time   = st.time_input("Heure fin *")
                                        week_type  = st.selectbox("Semaine",
                                                                   ["Toutes","Paire","Impaire"])
                                    with col2:
                                        course_sel = st.selectbox("Cours *", options=courses,
                                                                   format_func=lambda c: c["name"])
                                        prof_sel   = st.selectbox("Professeur *", options=professors,
                                                                   format_func=lambda p: p["name"])
                                        room       = st.text_input("Salle")

                                    if st.form_submit_button("Ajouter", type="primary"):
                                        if start_time >= end_time:
                                            st.error("L'heure de fin doit être après l'heure de début.")
                                        else:
                                            start_str = start_time.strftime("%H:%M")
                                            end_str   = end_time.strftime("%H:%M")
                                            try:
                                                conflicts = ScheduleQueries.check_conflict(
                                                    cls_sel["id"], day, start_str, end_str)
                                                if conflicts:
                                                    st.error("⚠️ Conflit d'horaire détecté !")
                                                else:
                                                    ScheduleQueries.create(
                                                        cls_sel["id"], day, start_str, end_str,
                                                        room.strip(), course_sel["id"],
                                                        prof_sel["id"], week_type)
                                                    st.success("✅ Créneau ajouté !"); st.rerun()
                                            except Exception as e:
                                                st.error(f"Erreur : {e}")

                        if schedules:
                            st.divider()
                            st.markdown("#### Supprimer un créneau")
                            for s in schedules:
                                start = str(s['start_time'])[:5]
                                end   = str(s['end_time'])[:5]
                                label = f"{s['day']} {start}–{end} | {s['course_name']} | {s['professor_name']}"
                                if st.button(f"🗑️ {label}", key=f"del_sched_{s['id']}"):
                                    ScheduleQueries.delete(s["id"])
                                    st.success("Créneau supprimé."); st.rerun()

    # ── COMMUNIQUÉS ───────────────────────────────────────────────────────────
    with tabs[5]:
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
                if st.form_submit_button("Publier", type="primary"):
                    if title.strip() and content.strip():
                        expires_dt = None
                        if expires:
                            from datetime import datetime
                            expires_dt = datetime.combine(expires, datetime.max.time())
                        AnnouncementQueries.create(
                            title.strip(), content.strip(), dept_id, is_pinned, expires_dt)
                        st.success("✅ Communiqué publié !"); st.rerun()
                    else:
                        st.error("Titre et contenu obligatoires.")

        for ann in announcements:
            with st.expander(f"{'📌 ' if ann.get('is_pinned') else ''}📢 {ann['title']}"):
                announcement_card(ann)
                if st.button("🗑️ Supprimer", key=f"del_ann_{ann['id']}"):
                    AnnouncementQueries.delete(ann["id"]); st.rerun()


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
else:
    st.error("Rôle non reconnu.")
