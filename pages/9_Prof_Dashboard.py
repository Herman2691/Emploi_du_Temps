# pages/9_Prof_Dashboard.py
import streamlit as st
from datetime import datetime
from utils.auth import require_prof_auth, get_current_user, logout, ROLE_LABELS
from utils.components import inject_global_css, dashboard_header
from utils.storage import (upload_pdf, delete_file, get_pdf_bytes,
                            COURSE_DOCS_BUCKET, TP_SUBMISSIONS_BUCKET)
from db.queries import (ProfessorExtQueries, CourseDocumentQueries,
                         TpAssignmentQueries, TpSubmissionQueries,
                         GradeQueries, StudentQueries, CourseQueries,
                         PromotionQueries, FacultyQueries, DepartmentQueries,
                         ScheduleQueries, AttendanceQueries,
                         ClassMessageQueries, GradeClaimQueries,
                         GradeAuditQueries, GradeModificationRequestQueries,
                         BulletinQueries)

inject_global_css()
require_prof_auth()

user    = get_current_user()
prof_id = user.get("professor_id")
uni_id  = user.get("university_id")

if not prof_id:
    st.error("Aucun profil professeur associé à ce compte. Contactez l'administrateur.")
    st.stop()


dashboard_header(
    "Espace Professeur",
    f"Bienvenue, {user['name']} — Gérez vos cours, TPs et notes",
    "👨‍🏫", "#7C3AED", "#6D28D9"
)

# ── Chargement des données de base ────────────────────────────────────────────
try:
    classes    = ProfessorExtQueries.get_classes(prof_id)   # classes où il enseigne
    courses    = ProfessorExtQueries.get_courses(prof_id)   # cours qu'il enseigne
    tps        = TpAssignmentQueries.get_by_professor(prof_id)
    docs       = CourseDocumentQueries.get_by_professor(prof_id)
    faculties  = FacultyQueries.get_by_university(uni_id) if uni_id else []
except Exception as e:
    st.error(f"Erreur chargement données : {e}")
    st.stop()

# Stats rapides
pending_subs = sum(
    int(tp.get("submissions_count", 0)) for tp in tps
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mes Classes", len(classes))
c2.metric("Mes Cours",   len(courses))
c3.metric("TPs créés",   len(tps))
c4.metric("Documents",   len(docs))

st.divider()

# ── Onglets ────────────────────────────────────────────────────────────────────
tab_docs, tab_tp, tab_notes, tab_classes, tab_presence, tab_messages, tab_claims = st.tabs([
    "📄 Cours & Documents",
    "📝 Travaux Pratiques",
    "📊 Notes",
    "👥 Mes Classes",
    "📍 Présences",
    "💬 Messages",
    "🔔 Réclamations",
])


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 1 : DOCUMENTS DE COURS
# ══════════════════════════════════════════════════════════════════════════════
with tab_docs:
    st.markdown("#### Déposer un document de cours (PDF)")

    if not courses:
        st.info("Aucun cours trouvé dans vos horaires. Contactez l'administrateur.")
    else:
        with st.expander("➕ Ajouter un document"):
            # Sélection en cascade : Faculté → Département → Promotion + Cours
            col_f, col_d = st.columns(2)
            with col_f:
                fac_sel = st.selectbox(
                    "Faculté *", options=faculties,
                    format_func=lambda f: f["name"],
                    index=None, placeholder="— Sélectionner —",
                    key="doc_fac"
                )
            with col_d:
                depts_doc = DepartmentQueries.get_by_faculty(fac_sel["id"]) if fac_sel else []
                dept_sel = st.selectbox(
                    "Département *", options=depts_doc,
                    format_func=lambda d: d["name"],
                    index=None, placeholder="— Sélectionner —",
                    key="doc_dept"
                )

            col_p, col_c = st.columns(2)
            with col_p:
                promos_doc = PromotionQueries.get_by_department(dept_sel["id"]) if dept_sel else []
                promo_sel = st.selectbox(
                    "Promotion destinataire *", options=promos_doc,
                    format_func=lambda p: f"{p['name']} ({p.get('academic_year','')})",
                    index=None, placeholder="— Sélectionner —",
                    key="doc_promo"
                )
            with col_c:
                courses_doc = CourseQueries.get_by_department(dept_sel["id"]) if dept_sel else []
                course_sel = st.selectbox(
                    "Cours *", options=courses_doc,
                    format_func=lambda c: f"{c['name']} ({c.get('code','—')})",
                    index=None, placeholder="— Sélectionner —",
                    key="doc_course"
                )

            with st.form("add_doc"):
                doc_title = st.text_input("Titre du document *",
                                          placeholder="ex: Cours 3 — Algorithmique")
                doc_desc  = st.text_area("Description (optionnel)")
                pdf_file  = st.file_uploader("Fichier PDF *", type=["pdf"])

                if st.form_submit_button("Uploader", type="primary"):
                    if not promo_sel or not course_sel:
                        st.error("Sélectionnez la faculté, le département, la promotion et le cours.")
                    elif not doc_title.strip() or not pdf_file:
                        st.error("Titre et fichier PDF obligatoires.")
                    else:
                        try:
                            file_bytes = pdf_file.read()
                            size_kb    = len(file_bytes) // 1024
                            url, _     = upload_pdf(
                                file_bytes, pdf_file.name,
                                COURSE_DOCS_BUCKET,
                                folder=f"prof_{prof_id}"
                            )
                            CourseDocumentQueries.create(
                                course_id=course_sel["id"],
                                professor_id=prof_id,
                                title=doc_title.strip(),
                                description=doc_desc.strip() or None,
                                file_url=url,
                                file_name=pdf_file.name,
                                file_size_kb=size_kb,
                                promotion_id=promo_sel["id"],
                            )
                            st.success("✅ Document uploadé avec succès !")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur upload : {e}")

    st.divider()
    st.markdown("#### Mes documents publiés")

    if not docs:
        st.info("Aucun document publié pour l'instant.")
    else:
        for doc in docs:
            col_info, col_link, col_del = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"""
                <div style="padding:0.5rem 0">
                    <div style="font-weight:600;color:#1E293B">{doc['title']}</div>
                    <div style="color:#64748B;font-size:0.8rem">
                        📘 {doc['course_name']} &nbsp;·&nbsp;
                        🎓 {doc.get('promotion_name','—')} &nbsp;·&nbsp;
                        📄 {doc['file_name']} &nbsp;·&nbsp;
                        💾 {doc.get('file_size_kb',0)} Ko
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_link:
                _pdf = get_pdf_bytes(doc["file_url"])
                if _pdf:
                    st.download_button("⬇️ Télécharger", _pdf,
                                       file_name=doc["file_name"],
                                       mime="application/pdf",
                                       key=f"dl_doc_{doc['id']}",
                                       use_container_width=True)
                else:
                    st.caption("Fichier introuvable")
            with col_del:
                if st.button("🗑️", key=f"del_doc_{doc['id']}",
                             help="Supprimer ce document"):
                    CourseDocumentQueries.delete(doc["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 : TRAVAUX PRATIQUES
# ══════════════════════════════════════════════════════════════════════════════
with tab_tp:
    col_create, col_list = st.columns([1, 2], gap="large")

    with col_create:
        st.markdown("#### ➕ Créer un TP")
        if not classes or not courses:
            st.info("Vous devez avoir des classes assignées et des cours dans votre département.")
        else:
            with st.form("create_tp"):
                tp_title   = st.text_input("Titre du TP *")
                tp_desc    = st.text_area("Consignes (texte)")
                tp_pdf     = st.file_uploader("Sujet PDF (optionnel)", type=["pdf"],
                                              key="tp_subject_pdf")
                tp_course  = st.selectbox(
                    "Cours *", options=courses,
                    format_func=lambda c: c["name"]
                )
                tp_class   = st.selectbox(
                    "Classe *", options=classes,
                    format_func=lambda c: f"{c['name']} ({c.get('promotion_name','')})"
                )
                tp_date    = st.date_input("Date limite *",
                                           min_value=datetime.today())
                tp_time    = st.time_input("Heure limite *")
                tp_max_mb  = st.number_input("Taille max PDF soumission (Mo)",
                                              min_value=1, max_value=50, value=10)

                if st.form_submit_button("Créer le TP", type="primary"):
                    if not tp_title.strip():
                        st.error("Le titre est obligatoire.")
                    else:
                        deadline = datetime.combine(tp_date, tp_time)
                        try:
                            # Upload du sujet PDF si fourni
                            subj_url = subj_name = None
                            if tp_pdf:
                                subj_url, _ = upload_pdf(
                                    tp_pdf.read(), tp_pdf.name,
                                    TP_SUBMISSIONS_BUCKET,
                                    folder=f"subjects/prof_{prof_id}"
                                )
                                subj_name = tp_pdf.name

                            TpAssignmentQueries.create(
                                title=tp_title.strip(),
                                description=tp_desc.strip() or None,
                                course_id=tp_course["id"],
                                professor_id=prof_id,
                                class_id=tp_class["id"],
                                deadline=deadline,
                                max_file_mb=int(tp_max_mb),
                                subject_url=subj_url,
                                subject_file_name=subj_name,
                            )
                            st.success("✅ TP créé !")
                            try:
                                from utils.notifications import notify_tp
                                from db.queries import UniversityQueries as _UQ
                                _uni = _UQ.get_by_id(user.get("university_id"))
                                _uni_name = _uni["name"] if _uni else "UniSchedule"
                                sent = notify_tp(
                                    class_id=tp_class["id"],
                                    tp_title=tp_title.strip(),
                                    course_name=tp_course["name"],
                                    deadline_str=deadline.strftime("%d/%m/%Y à %H:%M"),
                                    description=tp_desc.strip() or None,
                                    university_name=_uni_name,
                                )
                                if sent > 0:
                                    st.info(f"📧 {sent} notification(s) email envoyée(s).")
                            except Exception:
                                pass
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

    with col_list:
        st.markdown("#### Mes TPs")
        if not tps:
            st.info("Aucun TP créé.")
        else:
            for tp in tps:
                deadline_dt = tp["deadline"]
                if isinstance(deadline_dt, str):
                    deadline_dt = datetime.fromisoformat(deadline_dt)
                is_expired  = deadline_dt < datetime.now() if deadline_dt else False
                status_icon = "🟢" if tp["is_open"] and not is_expired else "🔴"
                status_txt  = "Ouvert" if tp["is_open"] and not is_expired else \
                              ("Expiré" if is_expired else "Fermé")

                with st.expander(
                    f"{status_icon} {tp['title']} — {tp['class_name']} "
                    f"({tp.get('submissions_count',0)} soumission(s))"
                ):
                    col_a, col_b = st.columns(2)
                    col_a.caption(f"📘 {tp['course_name']}")
                    col_a.caption(f"⏰ Deadline : {deadline_dt.strftime('%d/%m/%Y %H:%M') if deadline_dt else '—'}")
                    col_b.caption(f"Statut : **{status_txt}**")

                    if tp["is_open"] and not is_expired:
                        if col_b.button("🔒 Fermer le dépôt",
                                        key=f"close_tp_{tp['id']}"):
                            TpAssignmentQueries.toggle_open(tp["id"], False)
                            st.rerun()
                    else:
                        if col_b.button("🔓 Rouvrir le dépôt",
                                        key=f"open_tp_{tp['id']}",
                                        type="primary"):
                            TpAssignmentQueries.toggle_open(tp["id"], True)
                            st.rerun()

                    st.divider()
                    st.markdown("**📥 Soumissions reçues**")

                    try:
                        submissions = TpSubmissionQueries.get_by_assignment(tp["id"])
                    except Exception as e:
                        st.error(str(e))
                        submissions = []

                    if not submissions:
                        st.caption("Aucune soumission pour l'instant.")
                    else:
                        for sub in submissions:
                            s_col1, s_col2, s_col3 = st.columns([3, 1, 2])
                            s_col1.markdown(
                                f"**{sub['student_name']}** "
                                f"({sub['student_number']})"
                            )
                            s_col1.caption(
                                f"Déposé le {sub['submitted_at'].strftime('%d/%m %H:%M') if sub.get('submitted_at') else '—'}"
                            )
                            with s_col2:
                                _spdf = get_pdf_bytes(sub["file_url"])
                                if _spdf:
                                    st.download_button("⬇️ PDF", _spdf,
                                                       file_name=sub.get("file_name","tp.pdf"),
                                                       mime="application/pdf",
                                                       key=f"dl_sub_{sub['id']}",
                                                       use_container_width=True)
                                else:
                                    st.caption("—")

                            with s_col3:
                                note_key  = f"grade_sub_{sub['id']}"
                                comment_k = f"comment_sub_{sub['id']}"
                                note_val  = st.number_input(
                                    "Note /20", min_value=0.0, max_value=20.0,
                                    value=float(sub["grade"]) if sub.get("grade") else 0.0,
                                    step=0.5, key=note_key
                                )
                                comment_v = st.text_input(
                                    "Commentaire", key=comment_k,
                                    value=sub.get("grade_comment") or ""
                                )
                                if st.button("💾 Noter",
                                             key=f"save_grade_{sub['id']}"):
                                    TpSubmissionQueries.grade(
                                        sub["id"], note_val, comment_v
                                    )
                                    st.success("✅ Note enregistrée !")
                                    st.rerun()
                            st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 3 : NOTES
# ══════════════════════════════════════════════════════════════════════════════
with tab_notes:
    from datetime import datetime, timezone as _tz

    def _hours_since(dt):
        if dt is None:
            return 999
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        return (datetime.now(_tz.utc) - dt).total_seconds() / 3600

    st.markdown("#### Gestion des notes")

    if not classes or not courses:
        st.info("Aucune classe ou cours trouvé dans vos horaires.")
    else:
        col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
        with col_sel1:
            notes_course = st.selectbox(
                "Cours", options=courses,
                format_func=lambda c: c["name"],
                key="notes_course_sel"
            )
        with col_sel2:
            notes_class = st.selectbox(
                "Salle", options=classes,
                format_func=lambda c: c["name"],
                key="notes_class_sel"
            )
        with col_sel3:
            exam_type = st.selectbox(
                "Type d'épreuve",
                ["Examen", "Contrôle Continu", "TP Noté", "Rattrapage"],
                key="notes_exam_type"
            )
        with col_sel4:
            notes_session = st.text_input(
                "Session",
                value="Principale",
                placeholder="ex: Janvier 2025",
                key="notes_session_name"
            )

        if notes_course and notes_class:
            try:
                students = StudentQueries.get_by_class(notes_class["id"])
                existing_grades = {
                    g["student_id"]: g
                    for g in (GradeQueries.get_by_course_and_class(
                        notes_course["id"], notes_class["id"]
                    ) or [])
                    if g.get("exam_type") == exam_type
                    and g.get("session_name") == (notes_session.strip() or "Principale")
                }
            except Exception as e:
                st.error(str(e))
                students = []; existing_grades = {}

            if not students:
                st.info("Aucun étudiant enregistré dans cette salle.")
            else:
                # ── Section 1 : Saisie / mise à jour groupée ──────────────────
                st.markdown(f"**{len(students)} étudiant(s) — {notes_course['name']}**")

                with st.form("publish_notes"):
                    max_grade = st.number_input("Note maximale", min_value=1.0,
                                                max_value=100.0, value=20.0, step=1.0)
                    _bulk_motif = st.text_input(
                        "Motif de saisie (obligatoire si modification d'une note existante)",
                        placeholder="ex: Saisie initiale des résultats",
                        key="bulk_motif"
                    )
                    note_inputs   = {}
                    comment_inputs = {}

                    for stu in students:
                        _ex = existing_grades.get(stu["id"])
                        _default_g = float(_ex["grade"]) if _ex else 0.0
                        c_n, c_g, c_c = st.columns([3, 1, 2])
                        c_n.markdown(
                            f"**{stu['full_name']}** "
                            f"<span style='color:#94A3B8;font-size:0.8rem'>"
                            f"({stu['student_number']})</span>",
                            unsafe_allow_html=True
                        )
                        note_inputs[stu["id"]] = c_g.number_input(
                            "Note", min_value=0.0,
                            max_value=float(max_grade),
                            value=_default_g, step=0.5,
                            key=f"note_{stu['id']}",
                            label_visibility="collapsed"
                        )
                        comment_inputs[stu["id"]] = c_c.text_input(
                            "Commentaire", key=f"cmnt_{stu['id']}",
                            value=_ex.get("comment","") if _ex else "",
                            label_visibility="collapsed",
                            placeholder="Commentaire (optionnel)"
                        )

                    if st.form_submit_button("💾 Enregistrer les notes", type="primary"):
                        _has_existing = any(
                            stu["id"] in existing_grades for stu in students
                        )
                        if _has_existing and not _bulk_motif.strip():
                            st.error("Le motif est obligatoire pour modifier des notes existantes.")
                        else:
                            try:
                                session_val = notes_session.strip() or "Principale"
                                for stu_id, grade_val in note_inputs.items():
                                    GradeQueries.upsert(
                                        student_id=stu_id,
                                        course_id=notes_course["id"],
                                        professor_id=prof_id,
                                        grade=grade_val,
                                        max_grade=max_grade,
                                        exam_type=exam_type,
                                        comment=comment_inputs.get(stu_id) or None,
                                        session_name=session_val,
                                        motif=_bulk_motif.strip() or "Saisie initiale",
                                    )
                                st.success(
                                    f"✅ Notes enregistrées pour {len(students)} étudiant(s) !"
                                )
                                try:
                                    from utils.notifications import notify_grade
                                    from db.queries import UniversityQueries as _UQ
                                    _uni = _UQ.get_by_id(user.get("university_id"))
                                    _uni_name = _uni["name"] if _uni else "UniSchedule"
                                    _notif_c = 0
                                    for stu_obj in students:
                                        if stu_obj.get("email"):
                                            notify_grade(
                                                student_email=stu_obj["email"],
                                                student_name=stu_obj["full_name"],
                                                course_name=notes_course["name"],
                                                grade=note_inputs.get(stu_obj["id"], 0),
                                                max_grade=max_grade,
                                                exam_type=exam_type,
                                                comment=comment_inputs.get(stu_obj["id"]) or None,
                                                university_name=_uni_name,
                                            )
                                            _notif_c += 1
                                    if _notif_c > 0:
                                        st.info(f"📧 {_notif_c} notification(s) envoyée(s).")
                                except Exception:
                                    pass
                            except Exception as e:
                                st.error(f"Erreur : {e}")

                # ── Section 1b : Soumettre les notes au département ───────────
                st.divider()
                _submit_session_val = notes_session.strip() or "Principale"

                _STATUS_CLR_P = {
                    "brouillon": "#64748B",
                    "soumis":    "#3B82F6",
                    "valide":    "#10B981",
                    "publie":    "#6D28D9",
                }
                _STATUS_LBL_P = {
                    "brouillon": "Brouillon",
                    "soumis":    "Soumis",
                    "valide":    "Validé",
                    "publie":    "Publié",
                }

                try:
                    _status_rows = GradeQueries.get_status_summary(
                        notes_class["id"], _submit_session_val
                    ) or []
                    _status_map  = {r["status"]: int(r["cnt"]) for r in _status_rows}
                except Exception:
                    _status_map = {}

                if _status_map:
                    st.markdown("**Statut des notes — session '" + _submit_session_val + "'**")
                    _scols = st.columns(len(_status_map))
                    for _i, (_st, _cnt) in enumerate(_status_map.items()):
                        _c  = _STATUS_CLR_P.get(_st, "#64748B")
                        _lb = _STATUS_LBL_P.get(_st, _st)
                        _scols[_i].markdown(
                            f"<div style='text-align:center;padding:0.5rem;"
                            f"background:{_c}15;border:1px solid {_c}44;"
                            f"border-radius:8px'>"
                            f"<div style='font-size:0.72rem;color:{_c};font-weight:600'>{_lb}</div>"
                            f"<div style='font-size:1.5rem;font-weight:700;color:{_c}'>{_cnt}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                _nb_brouillon = _status_map.get("brouillon", 0)
                _nb_soumis    = _status_map.get("soumis",    0)
                _nb_valide    = _status_map.get("valide",    0)
                _nb_publie    = _status_map.get("publie",    0)

                if _nb_brouillon > 0:
                    st.caption(
                        "Soumettez vos notes au département pour qu'elles soient validées "
                        "puis publiées aux étudiants."
                    )
                    if st.button(
                        f"📤 Soumettre {_nb_brouillon} note(s) au département",
                        type="primary", key="submit_notes_btn"
                    ):
                        try:
                            _submitted = GradeQueries.submit_session(
                                prof_id,
                                notes_class["id"],
                                _submit_session_val,
                            )
                            st.success(
                                f"✅ {_submitted} note(s) soumise(s) au département "
                                f"pour validation !"
                            )
                            st.rerun()
                        except Exception as _se:
                            st.error(f"Erreur soumission : {_se}")
                elif _nb_soumis > 0:
                    st.info(
                        f"✅ {_nb_soumis} note(s) soumise(s) — en attente de validation "
                        f"par le département."
                    )
                elif _nb_valide > 0:
                    st.info(
                        f"✅ {_nb_valide} note(s) validée(s) — en attente de publication "
                        f"par le département."
                    )
                elif _nb_publie > 0 and _nb_brouillon == 0:
                    st.success("✅ Toutes les notes sont publiées.")

                # ── Section 2 : Modification individuelle avec règle 48h ───────
                if existing_grades:
                    st.divider()
                    st.markdown("#### ✏️ Modifier une note existante")
                    st.caption(
                        "Vous pouvez modifier directement une note saisie il y a **moins de 48h** "
                        "(avec motif obligatoire).  \n"
                        "Au-delà de 48h, une **demande de validation** est envoyée à "
                        "l'administrateur du département."
                    )

                    for stu in students:
                        _ex = existing_grades.get(stu["id"])
                        if not _ex:
                            continue

                        _created = _ex.get("created_at")
                        _age_h   = _hours_since(_created)
                        _within  = _age_h < 48
                        _badge   = (
                            f"🟢 Saisie il y a {int(_age_h)}h"
                            if _within else
                            f"🔴 Saisie il y a {int(_age_h)}h (validation admin requise)"
                        )

                        _edit_key = f"show_edit_{_ex.get('id', stu['id'])}"
                        with st.expander(
                            f"{'✏️' if _within else '📋'} {stu['full_name']} "
                            f"— Note actuelle : **{_ex['grade']:.1f}/{_ex['max_grade']:.0f}** "
                            f"· {_badge}"
                        ):
                            # ── Historique de cette note ──────────────────────
                            with st.expander("📜 Historique des modifications"):
                                try:
                                    _hist = GradeAuditQueries.get_by_grade(_ex["id"])
                                except Exception:
                                    _hist = []
                                if not _hist:
                                    st.caption("Aucune modification enregistrée.")
                                else:
                                    _ACTION_LABELS = {
                                        "create":            "✅ Saisie initiale",
                                        "update":            "✏️ Modification directe",
                                        "request_approved":  "✔️ Modification approuvée",
                                        "request_rejected":  "❌ Demande rejetée",
                                    }
                                    for _h in _hist:
                                        _at = _h.get("changed_at")
                                        _at_str = _at.strftime("%d/%m/%Y %H:%M") if _at else "—"
                                        _act = _ACTION_LABELS.get(_h.get("action","update"),
                                                                   _h.get("action","—"))
                                        st.markdown(
                                            f"**{_at_str}** · {_act}  \n"
                                            f"Ancienne note : `{_h.get('old_grade','—')}` → "
                                            f"Nouvelle : `{_h.get('new_grade','—')}/{_h.get('max_grade','—')}`  \n"
                                            f"Motif : *{_h.get('motif') or '—'}*  \n"
                                            f"Par : {_h.get('professor_name') or _h.get('reviewed_by_name','—')}"
                                        )
                                        st.divider()

                            # ── Formulaire de modification ────────────────────
                            with st.form(f"modify_grade_{_ex.get('id', stu['id'])}"):
                                _new_g = st.number_input(
                                    "Nouvelle note *",
                                    min_value=0.0, max_value=100.0,
                                    value=float(_ex["grade"]), step=0.5
                                )
                                _new_max = st.number_input(
                                    "Nouvelle note max",
                                    min_value=1.0, max_value=100.0,
                                    value=float(_ex["max_grade"]), step=1.0
                                )
                                _new_cmt = st.text_input(
                                    "Commentaire",
                                    value=_ex.get("comment") or ""
                                )
                                _motif = st.text_area(
                                    "Motif de modification * (obligatoire)",
                                    placeholder="ex: Erreur de saisie, correction après délibération…"
                                )

                                if _within:
                                    _btn_label = "💾 Modifier directement (< 48h)"
                                else:
                                    _btn_label = "📋 Soumettre une demande (> 48h)"

                                if st.form_submit_button(_btn_label, type="primary"):
                                    if not _motif.strip():
                                        st.error("Le motif est obligatoire.")
                                    else:
                                        try:
                                            if _within:
                                                GradeQueries.update_direct(
                                                    grade_id=_ex["id"],
                                                    new_grade=_new_g,
                                                    new_max=_new_max,
                                                    new_comment=_new_cmt or None,
                                                    motif=_motif.strip(),
                                                    professor_id=prof_id,
                                                )
                                                st.success("✅ Note modifiée avec succès !")
                                            else:
                                                GradeModificationRequestQueries.create(
                                                    grade_id=_ex["id"],
                                                    professor_id=prof_id,
                                                    requested_grade=_new_g,
                                                    requested_max=_new_max,
                                                    requested_comment=_new_cmt or None,
                                                    motif=_motif.strip(),
                                                    current_grade=float(_ex["grade"]),
                                                    current_max=float(_ex["max_grade"]),
                                                    current_comment=_ex.get("comment"),
                                                )
                                                st.info(
                                                    "📋 Demande envoyée à l'administrateur "
                                                    "du département. Elle sera traitée sous peu."
                                                )
                                            st.rerun()
                                        except Exception as _e:
                                            st.error(f"Erreur : {_e}")

        # ── Export / Import Excel des notes ──────────────────────────────────
        if notes_course and notes_class:
            import io as _io_notes
            import pandas as _pd_notes

            _session_xl  = notes_session.strip() or "Principale"
            _students_xl = StudentQueries.get_by_class(notes_class["id"]) or []
            _fname_base  = (
                f"notes_{notes_class['name'].replace(' ','_')}"
                f"_{notes_course['name'].replace(' ','_')}"
                f"_{_session_xl.replace(' ','_')}"
            )

            # ── Export ────────────────────────────────────────────────────────
            with st.expander("📊 Exporter les notes vers Excel"):
                _ecol1, _ecol2 = st.columns(2)

                # Modèle vide
                _tmpl_buf = _io_notes.BytesIO()
                _pd_notes.DataFrame([{
                    "numéro étudiant": s["student_number"],
                    "nom":             s["full_name"],
                    "note":            "",
                    "note_max":        20,
                    "commentaire":     "",
                } for s in _students_xl]).to_excel(
                    _tmpl_buf, index=False, engine="openpyxl"
                )
                _ecol1.download_button(
                    "📋 Modèle vide",
                    data=_tmpl_buf.getvalue(),
                    file_name=f"{_fname_base}_modele.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Feuille vierge avec la liste des étudiants à remplir",
                )

                # Export des notes actuelles (session + type d'épreuve sélectionnés)
                _exp_buf = _io_notes.BytesIO()
                _pd_notes.DataFrame([{
                    "numéro étudiant": s["student_number"],
                    "nom":             s["full_name"],
                    "note":            (
                        float(existing_grades[s["id"]]["grade"])
                        if s["id"] in existing_grades else ""
                    ),
                    "note_max":        (
                        float(existing_grades[s["id"]]["max_grade"])
                        if s["id"] in existing_grades else 20
                    ),
                    "commentaire":     (
                        existing_grades[s["id"]].get("comment") or ""
                        if s["id"] in existing_grades else ""
                    ),
                    "session":         _session_xl,
                    "type_epreuve":    exam_type,
                } for s in _students_xl]).to_excel(
                    _exp_buf, index=False, engine="openpyxl"
                )
                _ecol2.download_button(
                    "📊 Notes actuelles",
                    data=_exp_buf.getvalue(),
                    file_name=f"{_fname_base}_{exam_type.replace(' ','_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help=(
                        f"Notes enregistrées pour la session '{_session_xl}' "
                        f"· {exam_type}"
                    ),
                )

            # ── Import ────────────────────────────────────────────────────────
            with st.expander("📥 Importer les notes depuis Excel"):
                st.caption(
                    f"Les notes importées seront enregistrées pour la session "
                    f"**{_session_xl}** · **{exam_type}** "
                    f"(configurés ci-dessus)."
                )

                _notes_file = st.file_uploader(
                    "Fichier Excel (.xlsx)", type=["xlsx"], key="import_notes_excel"
                )
                if _notes_file:
                    try:
                        _df_n = _pd_notes.read_excel(
                            _notes_file, engine="openpyxl", dtype=str
                        )
                        _df_n.columns = (
                            _df_n.columns.str.strip().str.lower()
                            .str.replace("é", "e", regex=False)
                            .str.replace("è", "e", regex=False)
                            .str.replace("_", "_", regex=False)
                            .str.replace(" ", "_", regex=False)
                        )
                        _col_map = {
                            "numero_etudiant": "student_number",
                            "note":            "grade",
                            "note_max":        "max_grade",
                            "commentaire":     "comment",
                        }
                        _df_n = _df_n.rename(columns=_col_map).fillna("")

                        if "student_number" not in _df_n.columns or "grade" not in _df_n.columns:
                            st.error(
                                "Colonnes requises : **numéro étudiant** et **note**. "
                                "Utilisez le modèle fourni."
                            )
                        else:
                            # Aperçu
                            _preview_cols = [
                                c for c in ["student_number","grade","max_grade","comment"]
                                if c in _df_n.columns
                            ]
                            st.dataframe(
                                _df_n[_preview_cols].head(8),
                                use_container_width=True, hide_index=True
                            )
                            st.caption(
                                f"{len(_df_n)} ligne(s) · "
                                f"Session : **{_session_xl}** · "
                                f"Type : **{exam_type}**"
                            )

                            # Note max — depuis la colonne ou via saisie
                            _has_max_col = "max_grade" in _df_n.columns
                            _max_imp_default = 20.0
                            if _has_max_col:
                                try:
                                    _max_imp_default = float(
                                        _df_n["max_grade"]
                                        .replace("", float("nan"))
                                        .dropna().iloc[0]
                                    )
                                except Exception:
                                    pass
                            _max_imp = st.number_input(
                                "Note maximale (si non présente dans le fichier)",
                                min_value=1.0, max_value=100.0,
                                value=_max_imp_default,
                                disabled=_has_max_col,
                                key="imp_max_grade",
                                help=(
                                    "La colonne 'note_max' du fichier sera utilisée "
                                    "si présente."
                                    if _has_max_col else
                                    "Entrez la note maximale appliquée à toute la feuille."
                                ),
                            )
                            _motif_imp = st.text_input(
                                "Motif d'import (obligatoire si notes existantes)",
                                placeholder="ex: Import depuis relevé papier",
                                key="imp_motif",
                            )

                            if st.button("✅ Importer", type="primary",
                                         key="btn_imp_notes"):
                                _stu_map = {
                                    s["student_number"]: s["id"]
                                    for s in StudentQueries.get_by_class(notes_class["id"])
                                }
                                _ok_n = _err_n = _skip_n = 0
                                for _, _row in _df_n.iterrows():
                                    _num = str(_row.get("student_number","")).strip().upper()
                                    _stu_id = _stu_map.get(_num)
                                    if not _stu_id:
                                        _skip_n += 1; continue
                                    _grade_str = str(_row.get("grade","")).strip()
                                    if not _grade_str:
                                        _skip_n += 1; continue
                                    try:
                                        _g_val = float(_grade_str.replace(",", "."))
                                        _mx = (
                                            float(str(_row.get("max_grade","")).replace(",","."))
                                            if _has_max_col and str(_row.get("max_grade","")).strip()
                                            else _max_imp
                                        )
                                        _cmt = str(_row.get("comment","")).strip() or None
                                        GradeQueries.upsert(
                                            student_id=_stu_id,
                                            course_id=notes_course["id"],
                                            professor_id=prof_id,
                                            grade=_g_val,
                                            max_grade=_mx,
                                            exam_type=exam_type,
                                            comment=_cmt,
                                            session_name=_session_xl,
                                            motif=_motif_imp.strip() or "Import Excel",
                                        )
                                        _ok_n += 1
                                    except Exception:
                                        _err_n += 1
                                _msg = f"✅ {_ok_n} note(s) importée(s)"
                                if _skip_n:
                                    _msg += f" · {_skip_n} ligne(s) ignorée(s) (N° inconnu ou note vide)"
                                if _err_n:
                                    _msg += f" · {_err_n} erreur(s)"
                                st.success(_msg) if not _err_n else st.warning(_msg)
                                st.rerun()
                    except Exception as _e:
                        st.error(f"Erreur lecture Excel : {_e}")


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 : MES CLASSES
# ══════════════════════════════════════════════════════════════════════════════
with tab_classes:
    if not classes:
        st.info("Aucune classe assignée. L'administrateur doit d'abord créer des horaires vous incluant.")
    else:
        for cls in classes:
            with st.expander(
                f"🏫 {cls['name']} — {cls.get('promotion_name','')} "
                f"({cls.get('academic_year','')})"
            ):
                try:
                    students = StudentQueries.get_by_class(cls["id"])
                except Exception:
                    students = []

                col_a, col_b = st.columns(2)
                col_a.metric("Étudiants inscrits", len(students))
                col_b.caption(f"Département : {cls.get('department_name','—')}")

                if students:
                    st.divider()
                    for stu in students:
                        st.caption(
                            f"👤 {stu['full_name']} "
                            f"({stu['student_number']})"
                        )


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 5 : PRÉSENCES
# ══════════════════════════════════════════════════════════════════════════════
with tab_presence:
    st.markdown("#### Appel des étudiants")
    st.caption("Sélectionnez une salle et un créneau pour prendre l'appel.")

    if not classes:
        st.info("Aucune salle assignée.")
    else:
        _pr_col1, _pr_col2 = st.columns(2)
        with _pr_col1:
            _pr_class = st.selectbox(
                "Salle *", options=classes,
                format_func=lambda c: f"{c['name']} ({c.get('promotion_name','')})",
                key="pr_class_sel"
            )
        with _pr_col2:
            _pr_schedules = []
            if _pr_class:
                try:
                    _pr_schedules = ScheduleQueries.get_by_class(_pr_class["id"])
                    _pr_schedules = [s for s in _pr_schedules
                                     if s.get("slot_status","actif") == "actif"
                                     and s.get("slot_type","cours") != "ferie"
                                     and s.get("professor_id") == prof_id]
                except Exception:
                    _pr_schedules = []
            _pr_slot = st.selectbox(
                "Créneau *", options=_pr_schedules,
                format_func=lambda s: (
                    f"{s['day']} {str(s.get('start_time',''))[:5]}–"
                    f"{str(s.get('end_time',''))[:5]} · {s['course_name']}"
                ),
                key="pr_slot_sel"
            ) if _pr_schedules else None
            if not _pr_schedules and _pr_class:
                st.info("Aucun créneau disponible pour cette salle.")

        if _pr_class and _pr_slot:
            try:
                _pr_students = StudentQueries.get_by_class(_pr_class["id"])
                _pr_existing = {
                    a["student_id"]: a["status"]
                    for a in AttendanceQueries.get_by_schedule(_pr_slot["id"])
                }
            except Exception as _e:
                st.error(str(_e)); _pr_students = []; _pr_existing = {}

            if not _pr_students:
                st.info("Aucun étudiant dans cette salle.")
            else:
                st.markdown(f"**{len(_pr_students)} étudiant(s) · "
                            f"{_pr_slot['course_name']} · "
                            f"{_pr_slot['day']} {str(_pr_slot.get('start_time',''))[:5]}**")
                st.divider()

                _STATUTS_PR = {
                    "present":  "✅ Présent",
                    "absent":   "❌ Absent",
                    "retard":   "⏰ En retard",
                    "justifie": "📋 Justifié",
                }

                _pr_vals = {}
                for _stu in _pr_students:
                    _cur = _pr_existing.get(_stu["id"], "present")
                    _c1, _c2 = st.columns([3, 2])
                    _c1.markdown(f"**{_stu['full_name']}** `{_stu['student_number']}`")
                    _pr_vals[_stu["id"]] = _c2.selectbox(
                        "Statut", list(_STATUTS_PR.keys()),
                        format_func=lambda s: _STATUTS_PR[s],
                        index=list(_STATUTS_PR.keys()).index(_cur),
                        key=f"pr_status_{_pr_slot['id']}_{_stu['id']}",
                        label_visibility="collapsed"
                    )

                st.divider()
                if st.button("💾 Enregistrer l'appel", type="primary", key="save_presence"):
                    _ok_pr = 0
                    for _sid, _sval in _pr_vals.items():
                        try:
                            AttendanceQueries.record(
                                _pr_slot["id"], _sid, _sval,
                                recorded_by=user["id"]
                            )
                            _ok_pr += 1
                        except Exception:
                            pass
                    st.success(f"✅ Appel enregistré pour {_ok_pr} étudiant(s) !")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 6 : MESSAGES
# ══════════════════════════════════════════════════════════════════════════════
with tab_messages:
    st.markdown("#### Messages aux classes")
    st.caption("Envoyez un message à une ou plusieurs salles.")

    if not classes:
        st.info("Aucune salle assignée.")
    else:
        with st.expander("✉️ Nouveau message"):
            with st.form("new_message"):
                _msg_class = st.selectbox(
                    "Salle destinataire *", options=classes,
                    format_func=lambda c: f"{c['name']} ({c.get('promotion_name','')})",
                )
                _msg_subj  = st.text_input("Objet *")
                _msg_body  = st.text_area("Message *", height=150)
                _msg_urg   = st.checkbox("🚨 Message urgent")
                if st.form_submit_button("Envoyer", type="primary"):
                    if _msg_subj.strip() and _msg_body.strip():
                        try:
                            ClassMessageQueries.create(
                                prof_id, _msg_class["id"],
                                _msg_subj.strip(), _msg_body.strip(), _msg_urg
                            )
                            st.success("✅ Message envoyé !")
                            st.rerun()
                        except Exception as _e:
                            st.error(f"Erreur : {_e}")
                    else:
                        st.error("Objet et message obligatoires.")

        st.divider()
        st.markdown("#### Messages envoyés")
        try:
            _sent_msgs = ClassMessageQueries.get_by_professor(prof_id)
        except Exception as _e:
            st.error(str(_e)); _sent_msgs = []

        if not _sent_msgs:
            st.info("Aucun message envoyé.")
        else:
            for _m in _sent_msgs:
                _urg_badge = "🚨 " if _m.get("is_urgent") else ""
                with st.expander(
                    f"{_urg_badge}**{_m['subject']}** → {_m['class_name']}  "
                    f"· {_m['created_at'].strftime('%d/%m/%Y %H:%M') if _m.get('created_at') else ''}"
                ):
                    st.markdown(_m["body"])
                    if st.button("🗑️ Supprimer", key=f"del_msg_{_m['id']}"):
                        ClassMessageQueries.delete(_m["id"])
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 7 : RÉCLAMATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_claims:
    st.markdown("#### Réclamations de notes")
    st.caption("Réclamations déposées par les étudiants sur vos notes.")

    try:
        _claims = GradeClaimQueries.get_pending_by_professor(prof_id)
    except Exception as _e:
        st.error(str(_e)); _claims = []

    if not _claims:
        st.success("✅ Aucune réclamation en attente.")
    else:
        st.metric("Réclamations en attente", len(_claims))
        st.divider()
        for _cl in _claims:
            with st.expander(
                f"⚠️ {_cl['student_name']} — {_cl['course_name']} "
                f"· {_cl['exam_type']} · {_cl['session_name']}"
            ):
                st.markdown(
                    f"**Note actuelle :** {_cl['grade']:.1f}/{_cl['max_grade']:.0f}  \n"
                    f"**Raison :** {_cl['reason']}"
                )
                with st.form(f"review_claim_{_cl['id']}"):
                    _new_decision = st.radio(
                        "Décision", ["accepted", "rejected"],
                        format_func=lambda s: "✅ Accepter" if s == "accepted"
                                              else "❌ Rejeter",
                        horizontal=True
                    )
                    _claim_resp = st.text_area("Réponse (obligatoire)")
                    if st.form_submit_button("Valider", type="primary"):
                        if not _claim_resp.strip():
                            st.error("Une réponse est obligatoire.")
                        else:
                            try:
                                GradeClaimQueries.review(
                                    _cl["id"], _new_decision,
                                    _claim_resp.strip(), prof_id
                                )
                                st.success("✅ Réclamation traitée !")
                                st.rerun()
                            except Exception as _e:
                                st.error(f"Erreur : {_e}")
