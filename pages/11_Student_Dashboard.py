# pages/11_Student_Dashboard.py
import streamlit as st
from datetime import datetime, timedelta
from utils.auth import require_student_auth, get_current_student, logout_student
from utils.components import (inject_global_css, announcement_card,
                               week_nav, render_schedule_table, dashboard_header)
from utils.storage import upload_pdf, get_pdf_bytes, get_pdf_base64, TP_SUBMISSIONS_BUCKET
from db.queries import (ScheduleQueries, TpAssignmentQueries,
                         TpSubmissionQueries, GradeQueries,
                         CourseDocumentQueries, AnnouncementQueries,
                         ClassMessageQueries, AttendanceQueries,
                         GradeClaimQueries, AcademicEnrollmentQueries,
                         StudentResultsQueries)

inject_global_css()
require_student_auth()

student = get_current_student()

_prenom = student.get("prenom") or ""
_nom    = student.get("nom") or student.get("full_name","")
_display_name = student.get("display_name") or " ".join(filter(None,[_prenom,_nom])) \
                or student.get("full_name","Étudiant")
_username = student.get("username") or student["student_number"]


try:
    from db.queries import AcademicYearQueries as _AYQ_stu
    from db.connection import execute_query as _eq_stu
    _uni_row_stu = _eq_stu("""
        SELECT u.id FROM universities u
        JOIN faculties f   ON f.university_id = u.id
        JOIN departments d ON d.faculty_id    = f.id
        JOIN promotions pr ON pr.department_id = d.id
        JOIN classes cl    ON cl.promotion_id  = pr.id
        WHERE cl.id = %s LIMIT 1
    """, (student.get("class_id"),), fetch="one")
    _ay_stu = (
        _AYQ_stu.get_current(_uni_row_stu["id"])
        if _uni_row_stu else None
    )
    _ay_label_stu = f" · 📅 {_ay_stu['label']}" if _ay_stu else ""
except Exception:
    _ay_label_stu = ""

dashboard_header(
    "Mon Espace Étudiant",
    f"Bonjour, {_display_name} — @{_username} · N° {student['student_number']}{_ay_label_stu}",
    "🎓", "#059669", "#047857"
)

class_id = student.get("class_id")

if not class_id:
    st.warning("Votre classe n'est pas encore assignée. Contactez l'administration.")
    st.stop()

def _mention_label(avg):
    if avg >= 18: return "Excellent"
    if avg >= 16: return "Très Bien"
    if avg >= 14: return "Bien"
    if avg >= 12: return "Assez Bien"
    if avg >= 10: return "Passable"
    return "Non admis"

def _mention_color(avg):
    if avg >= 16: return "#6D28D9"
    if avg >= 14: return "#059669"
    if avg >= 12: return "#10B981"
    if avg >= 10: return "#F59E0B"
    return "#EF4444"

# ── Onglets ────────────────────────────────────────────────────────────────────
tab_edt, tab_tp, tab_notes, tab_cours, tab_bulletin, tab_presence, tab_messages, tab_parcours = st.tabs([
    "📅 Mon Horaire",
    "📝 Mes TPs",
    "📊 Mes Notes",
    "📚 Cours & Documents",
    "🎓 Mon Bulletin",
    "📍 Mon Assiduité",
    "💬 Messages",
    "📈 Mon Parcours",
])


with tab_edt:
    try:
        schedules = ScheduleQueries.get_by_class(class_id)
    except Exception as e:
        st.error(f"Erreur : {e}")
        schedules = []

    # Load university logo for this class
    try:
        from db.connection import execute_query as _eq
        from utils.components import get_logo_display_url as _gldurl
        _uni_row = _eq("""
            SELECT u.photo_url, u.primary_color, u.name as uni_name
            FROM universities u
            JOIN faculties f ON f.university_id=u.id
            JOIN departments d ON d.faculty_id=f.id
            JOIN promotions pr ON pr.department_id=d.id
            JOIN classes cl ON cl.promotion_id=pr.id
            WHERE cl.id=%s LIMIT 1
        """, (class_id,), fetch="one")
        _uni_logo = _gldurl((_uni_row or {}).get("photo_url","")) if _uni_row else None
    except Exception:
        _uni_logo = None

    if _uni_logo:
        _lc1, _lc2 = st.columns([1, 8])
        with _lc1:
            st.image(_uni_logo, width=60)

    if not schedules:
        st.info("📭 Aucun cours planifié pour votre classe.")
    else:
        _dd_stu, _wt_stu, _wn_stu, _mon_stu = week_nav("stu_week")
        _sat_stu = _mon_stu + timedelta(days=6)
        filtered = []
        for _s in schedules:
            if _s.get("week_type") not in ("Toutes", _wt_stu):
                continue
            _vf = _s.get("valid_from")
            _vu = _s.get("valid_until")
            if _vf is not None and _sat_stu < _vf:
                continue
            if _vu is not None and _mon_stu > _vu:
                continue
            filtered.append(_s)

        # ── Course filter ─────────────────────────────────────────────────────
        _course_names = sorted(set(s["course_name"] for s in schedules if s.get("course_name")))
        _filter_course = st.selectbox(
            "Filtrer par matière",
            ["Toutes"] + _course_names,
            key="stu_course_filter"
        )
        if _filter_course != "Toutes":
            filtered = [s for s in filtered if s.get("course_name") == _filter_course]

        render_schedule_table(filtered, _dd_stu)

        # ── iCal export ───────────────────────────────────────────────────────
        try:
            from utils.ical_export import generate_ical as _gen_ical_stu
            _ics_stu = _gen_ical_stu(schedules, student.get("class_name", "Classe"))
            st.download_button(
                "📅 Ajouter à mon calendrier",
                data=_ics_stu,
                file_name="mon_horaire.ics",
                mime="text/calendar",
            )
        except Exception:
            pass

    # Annonces
    try:
        announcements = AnnouncementQueries.get_by_class(class_id)
    except Exception:
        announcements = []
    if announcements:
        st.divider()
        st.markdown("#### 📢 Communiqués")
        for ann in announcements:
            announcement_card(ann)


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 : TRAVAUX PRATIQUES
# ══════════════════════════════════════════════════════════════════════════════
with tab_tp:
    try:
        open_tps  = TpAssignmentQueries.get_open_by_class(class_id)
        all_tps   = TpAssignmentQueries.get_by_class(class_id)
        my_subs   = TpSubmissionQueries.get_by_student(student["id"])
    except Exception as e:
        st.error(f"Erreur : {e}")
        open_tps = all_tps = my_subs = []

    submitted_ids = {s["tp_assignment_id"] for s in my_subs}

    col_open, col_hist = st.columns([3, 2], gap="large")

    with col_open:
        st.markdown("#### 📬 TPs ouverts")
        if not open_tps:
            st.info("Aucun TP en cours pour votre classe.")
        else:
            for tp in open_tps:
                deadline_dt = tp["deadline"]
                if isinstance(deadline_dt, str):
                    deadline_dt = datetime.fromisoformat(deadline_dt)

                already_submitted = tp["id"] in submitted_ids
                status_badge = (
                    "✅ Déjà soumis"
                    if already_submitted
                    else "⚠️ Non soumis"
                )

                with st.expander(
                    f"📝 {tp['title']} — {status_badge}"
                ):
                    st.caption(f"📘 {tp['course_name']}")
                    st.caption(
                        f"⏰ Deadline : "
                        f"{deadline_dt.strftime('%d/%m/%Y à %H:%M') if deadline_dt else '—'}"
                    )
                    if tp.get("description"):
                        st.markdown(
                            f"<p style='color:#475569;font-size:0.875rem'>"
                            f"{tp['description']}</p>",
                            unsafe_allow_html=True
                        )

                    if tp.get("subject_url"):
                        _subj_bytes = get_pdf_bytes(tp["subject_url"])
                        _subj_name  = tp.get("subject_file_name", "sujet.pdf")
                        col_sdl, col_sview, _ = st.columns([1, 1, 3])
                        with col_sdl:
                            if _subj_bytes:
                                st.download_button(
                                    "⬇️ Sujet PDF",
                                    _subj_bytes,
                                    file_name=_subj_name,
                                    mime="application/pdf",
                                    key=f"dl_subj_{tp['id']}",
                                    use_container_width=True,
                                )
                        with col_sview:
                            _sview_key = f"show_subj_{tp['id']}"
                            if st.button("👁️ Lire le sujet",
                                         key=f"btn_subj_{tp['id']}",
                                         use_container_width=True):
                                st.session_state[_sview_key] = \
                                    not st.session_state.get(_sview_key, False)
                        if st.session_state.get(f"show_subj_{tp['id']}"):
                            _subj_b64 = get_pdf_base64(tp["subject_url"])
                            if _subj_b64:
                                st.markdown(
                                    f'<iframe src="{_subj_b64}" '
                                    f'width="100%" height="680px" '
                                    f'style="border:1px solid #E2E8F0;'
                                    f'border-radius:10px;margin-top:0.5rem">'
                                    f'</iframe>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.error("Fichier sujet introuvable.")
                        st.divider()

                    if already_submitted:
                        existing = next(
                            (s for s in my_subs
                             if s["tp_assignment_id"] == tp["id"]), None
                        )
                        if existing:
                            st.success(
                                f"Fichier déposé : **{existing['file_name']}**"
                            )
                            if existing.get("grade") is not None:
                                st.info(
                                    f"Note reçue : **{existing['grade']}/20** "
                                    + (f"— {existing['grade_comment']}"
                                       if existing.get("grade_comment") else "")
                                )
                    else:
                        pdf_upload = st.file_uploader(
                            "Déposer votre PDF",
                            type=["pdf"],
                            key=f"upload_tp_{tp['id']}"
                        )
                        if st.button("📤 Soumettre",
                                     key=f"submit_tp_{tp['id']}",
                                     type="primary"):
                            if not pdf_upload:
                                st.error("Sélectionnez un fichier PDF.")
                            else:
                                max_mb = tp.get("max_file_mb", 10)
                                size_kb = len(pdf_upload.read()) // 1024
                                pdf_upload.seek(0)
                                if size_kb > max_mb * 1024:
                                    st.error(
                                        f"Fichier trop lourd (max {max_mb} Mo)."
                                    )
                                else:
                                    try:
                                        file_bytes = pdf_upload.read()
                                        url, _ = upload_pdf(
                                            file_bytes,
                                            pdf_upload.name,
                                            TP_SUBMISSIONS_BUCKET,
                                            folder=f"tp_{tp['id']}"
                                        )
                                        TpSubmissionQueries.submit(
                                            tp_assignment_id=tp["id"],
                                            student_id=student["id"],
                                            file_url=url,
                                            file_name=pdf_upload.name,
                                            file_size_kb=size_kb,
                                        )
                                        st.success("✅ TP soumis avec succès !")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur upload : {e}")

    with col_hist:
        st.markdown("#### 📋 Historique")
        if not my_subs:
            st.caption("Aucune soumission.")
        else:
            for sub in my_subs:
                status = "✅" if sub.get("grade") is not None else "⏳"
                deadline_dt = sub.get("deadline")
                st.markdown(
                    f"{status} **{sub['tp_title']}**  \n"
                    f"<span style='color:#94A3B8;font-size:0.78rem'>"
                    f"📘 {sub['course_name']} · "
                    f"Déposé le {sub['submitted_at'].strftime('%d/%m') if sub.get('submitted_at') else '—'}"
                    + (f" · Note : **{sub['grade']}/20**" if sub.get("grade") is not None else "")
                    + "</span>",
                    unsafe_allow_html=True
                )
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 3 : MES NOTES
# ══════════════════════════════════════════════════════════════════════════════
with tab_notes:
    try:
        grades = GradeQueries.get_by_student(student["id"])
    except Exception as e:
        st.error(str(e))
        grades = []

    if not grades:
        st.info("Aucune note publiée pour l'instant.")
    else:
        # Moyenne générale
        vals = [g["grade"] / g["max_grade"] * 20
                for g in grades if g.get("max_grade")]
        avg = sum(vals) / len(vals) if vals else 0

        col_avg, _ = st.columns([1, 3])
        col_avg.metric("Moyenne générale", f"{avg:.2f}/20")
        st.divider()

        # Grouper par cours
        by_course = {}
        for g in grades:
            cn = g["course_name"]
            by_course.setdefault(cn, []).append(g)

        for course_name, course_grades in by_course.items():
            with st.expander(f"📘 {course_name}"):
                for g in course_grades:
                    col_type, col_grade, col_comment, col_claim = st.columns([2, 1, 2, 1])
                    col_type.markdown(
                        f"**{g['exam_type']}**  \n"
                        f"<span style='color:#94A3B8;font-size:0.78rem'>"
                        f"Prof : {g['professor_name']}</span>",
                        unsafe_allow_html=True
                    )
                    note_color = (
                        "#10B981" if g["grade"] >= g["max_grade"] * 0.7
                        else "#F59E0B" if g["grade"] >= g["max_grade"] * 0.5
                        else "#EF4444"
                    )
                    col_grade.markdown(
                        f"<div style='font-size:1.4rem;font-weight:700;"
                        f"color:{note_color}'>{g['grade']:.1f}"
                        f"<span style='font-size:0.75rem;color:#94A3B8'>"
                        f"/{g['max_grade']:.0f}</span></div>",
                        unsafe_allow_html=True
                    )
                    if g.get("comment"):
                        col_comment.caption(f"💬 {g['comment']}")
                    _claim_key = f"show_claim_{g['id']}"
                    if col_claim.button("⚠️ Réclamer", key=f"btn_claim_{g['id']}",
                                        help="Contester cette note"):
                        st.session_state[_claim_key] = not st.session_state.get(_claim_key, False)
                    if st.session_state.get(_claim_key):
                        with st.form(f"claim_form_{g['id']}"):
                            _reason = st.text_area("Motif de la réclamation *")
                            if st.form_submit_button("Envoyer la réclamation", type="primary"):
                                if _reason.strip():
                                    try:
                                        GradeClaimQueries.create(
                                            g["id"], student["id"], _reason.strip()
                                        )
                                        st.success("✅ Réclamation envoyée !")
                                        st.session_state[_claim_key] = False
                                        st.rerun()
                                    except Exception as _e:
                                        st.error(f"Erreur : {_e}")
                                else:
                                    st.error("Le motif est obligatoire.")


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 : COURS & DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_cours:
    try:
        docs = CourseDocumentQueries.get_by_class(class_id)
    except Exception as e:
        st.error(str(e))
        docs = []

    if not docs:
        st.info("📭 Aucun document de cours disponible pour l'instant.")
    else:
        # Grouper par cours
        by_course = {}
        for d in docs:
            cn = d["course_name"]
            by_course.setdefault(cn, []).append(d)

        for course_name, course_docs in by_course.items():
            st.markdown(f"#### 📘 {course_name}")
            for doc in course_docs:
                with st.expander(
                    f"📄 {doc['title']} — 👨‍🏫 {doc['professor_name']}"
                ):
                    st.caption(
                        f"📄 {doc['file_name']} · "
                        f"💾 {doc.get('file_size_kb',0)} Ko"
                    )
                    if doc.get("description"):
                        st.caption(doc["description"])
                    col_view, col_dl, _ = st.columns([1, 1, 3])
                    _state_key = f"show_doc_{doc['id']}"
                    with col_view:
                        if st.button("👁️ Lire", key=f"btn_view_{doc['id']}",
                                     use_container_width=True):
                            st.session_state[_state_key] = \
                                not st.session_state.get(_state_key, False)
                    with col_dl:
                        _pdf = get_pdf_bytes(doc["file_url"])
                        if _pdf:
                            st.download_button("⬇️ Télécharger", _pdf,
                                               file_name=doc["file_name"],
                                               mime="application/pdf",
                                               key=f"dl_doc_{doc['id']}",
                                               use_container_width=True)
                        else:
                            st.caption("Fichier indisponible")
                    if st.session_state.get(_state_key):
                        _b64 = get_pdf_base64(doc["file_url"])
                        if _b64:
                            st.markdown(
                                f'<iframe src="{_b64}" '
                                f'width="100%" height="680px" '
                                f'style="border:1px solid #E2E8F0;'
                                f'border-radius:10px;margin-top:0.5rem">'
                                f'</iframe>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error("Fichier PDF introuvable sur le serveur.")
            st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 5 : MON BULLETIN
# ══════════════════════════════════════════════════════════════════════════════
with tab_bulletin:
    try:
        pub_sessions = GradeQueries.get_published_sessions_by_student(student["id"])
    except Exception as e:
        st.error(str(e)); pub_sessions = []

    if not pub_sessions:
        st.info(
            "Aucun bulletin publié pour l'instant. "
            "Les résultats apparaîtront ici une fois que votre département les aura publiés."
        )
    else:
        session_choices = [s["session_name"] for s in pub_sessions]
        selected_session = st.selectbox(
            "Sélectionner une session", options=session_choices,
            key="bulletin_session_sel"
        )

        if selected_session:
            try:
                bulletin_grades = GradeQueries.get_bulletin_by_student(
                    student["id"], selected_session
                )
            except Exception as e:
                st.error(str(e)); bulletin_grades = []

            if not bulletin_grades:
                st.info("Aucune note disponible pour cette session.")
            else:
                # Agréger par cours
                by_course_b = {}
                for g in bulletin_grades:
                    cn = g["course_name"]
                    if cn not in by_course_b:
                        by_course_b[cn] = {
                            "weight": float(g.get("course_weight") or 1.0),
                            "exams": [],
                        }
                    norm = (g["grade"] / g["max_grade"] * 20
                            if g.get("max_grade") else 0.0)
                    by_course_b[cn]["exams"].append({
                        "type": g["exam_type"],
                        "grade": g["grade"],
                        "max": g["max_grade"],
                        "norm": norm,
                        "comment": g.get("comment"),
                        "prof": g.get("professor_name", "—"),
                    })

                for cn, data in by_course_b.items():
                    exs = data["exams"]
                    data["avg20"] = sum(e["norm"] for e in exs) / len(exs)

                total_w_b = sum(d["weight"] for d in by_course_b.values())
                overall_avg = (
                    sum(d["avg20"] * d["weight"] for d in by_course_b.values())
                    / total_w_b if total_w_b > 0 else 0.0
                )

                # Rang dans la classe
                try:
                    rank_val = GradeQueries.get_class_rank(
                        student["id"], class_id, selected_session
                    )
                except Exception:
                    rank_val = None

                # ── En-tête du bulletin ───────────────────────────────────────
                men_label = _mention_label(overall_avg)
                men_color = _mention_color(overall_avg)
                rank_html = (
                    f"<div><div style='font-size:0.75rem;color:#94A3B8'>Rang</div>"
                    f"<div style='font-size:1.2rem;font-weight:600;color:#1E293B'>"
                    f"{rank_val}</div></div>"
                    if rank_val is not None else ""
                )

                # Décision officielle enregistrée par le département
                try:
                    _dec_row = StudentResultsQueries.get_by_student_session(
                        student["id"], selected_session
                    )
                    _decision_val = (_dec_row.get("decision") if _dec_row else None)
                except Exception:
                    _decision_val = None

                _DEC_CFG = {
                    "Admis":     ("✅", "#059669", "#D1FAE5"),
                    "Session 2": ("⚠️", "#D97706", "#FEF3C7"),
                    "Ajourné":   ("❌", "#DC2626", "#FEE2E2"),
                }
                _dec_icon, _dec_clr, _dec_bg = _DEC_CFG.get(
                    _decision_val, ("", "#64748B", "#F1F5F9")
                )
                _decision_html = (
                    f"<div style='margin-left:auto'>"
                    f"<div style='font-size:0.75rem;color:#94A3B8'>Décision officielle</div>"
                    f"<div style='background:{_dec_bg};color:{_dec_clr};"
                    f"padding:4px 14px;border-radius:20px;font-weight:700;"
                    f"font-size:1rem;display:inline-block;margin-top:2px'>"
                    f"{_dec_icon} {_decision_val}</div></div>"
                ) if _decision_val else ""

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{men_color}22,{men_color}11);
                            border:1px solid {men_color}44;border-radius:12px;
                            padding:1rem 1.5rem;margin-bottom:1rem">
                    <div style="font-size:0.85rem;color:#64748B;margin-bottom:0.5rem">
                        Session : <strong>{selected_session}</strong>
                    </div>
                    <div style="display:flex;gap:2rem;align-items:center;flex-wrap:wrap">
                        <div>
                            <div style="font-size:0.75rem;color:#94A3B8">Moyenne générale</div>
                            <div style="font-size:2rem;font-weight:700;color:{men_color}">
                                {overall_avg:.2f}
                                <span style="font-size:1rem;color:#94A3B8">/20</span>
                            </div>
                        </div>
                        <div>
                            <div style="font-size:0.75rem;color:#94A3B8">Mention</div>
                            <div style="font-size:1.2rem;font-weight:600;color:{men_color}">
                                {men_label}
                            </div>
                        </div>
                        {rank_html}
                        {_decision_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.divider()

                # ── Détail par cours ──────────────────────────────────────────
                for cn, data in sorted(by_course_b.items()):
                    avg_c = data["avg20"]
                    with st.expander(
                        f"📘 {cn}  —  {avg_c:.1f}/20 · {_mention_label(avg_c)}"
                    ):
                        for exam in data["exams"]:
                            c_type, c_grade, c_comment = st.columns([2, 1, 3])
                            c_type.markdown(
                                f"**{exam['type']}**  \n"
                                f"<span style='color:#94A3B8;font-size:0.78rem'>"
                                f"Prof : {exam['prof']}</span>",
                                unsafe_allow_html=True
                            )
                            c_grade.markdown(
                                f"<div style='font-size:1.4rem;font-weight:700;"
                                f"color:{_mention_color(exam['norm'])}'>"
                                f"{exam['grade']:.1f}"
                                f"<span style='font-size:0.75rem;color:#94A3B8'>"
                                f"/{exam['max']:.0f}</span></div>",
                                unsafe_allow_html=True
                            )
                            if exam.get("comment"):
                                c_comment.caption(f"💬 {exam['comment']}")

                # ── Export PDF du bulletin ────────────────────────────────────
                st.divider()
                try:
                    from utils.pdf_export import generate_bulletin_pdf
                    from db.queries import ClassQueries as _ClsQ
                    _cls_info = _ClsQ.get_by_id(class_id)
                    _pdf_bul = generate_bulletin_pdf(
                        student_name=_display_name,
                        student_number=student["student_number"],
                        class_name=_cls_info["name"] if _cls_info else "—",
                        promotion_name=_cls_info.get("promotion_name","—") if _cls_info else "—",
                        university_name=_cls_info.get("university_name","UniSchedule") if _cls_info else "UniSchedule",
                        session_name=selected_session,
                        grades_by_course=by_course_b,
                        overall_avg=overall_avg,
                        mention=men_label,
                        rank=rank_val,
                    )
                    st.download_button(
                        "📄 Télécharger le bulletin PDF",
                        data=_pdf_bul,
                        file_name=f"bulletin_{student['student_number']}_{selected_session}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                    )
                except Exception as _e:
                    st.caption(f"Export PDF indisponible : {_e}")


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 6 : MON ASSIDUITÉ
# ══════════════════════════════════════════════════════════════════════════════
with tab_presence:
    st.markdown("#### Mon assiduité")
    try:
        _att_stats = AttendanceQueries.get_student_stats(student["id"], class_id)
    except Exception as _e:
        st.error(str(_e)); _att_stats = []

    if not _att_stats:
        st.info("Aucune donnée d'assiduité disponible pour l'instant.")
    else:
        _total_p  = sum(int(r.get("presences",0) or 0) for r in _att_stats)
        _total_a  = sum(int(r.get("absences",0) or 0) for r in _att_stats)
        _total_s  = _total_p + _total_a
        _taux_g   = round(_total_p / _total_s * 100, 1) if _total_s else 0

        _ca, _cb, _cc = st.columns(3)
        _ca.metric("Séances assistées", _total_p)
        _cb.metric("Absences",          _total_a)
        _cc.metric("Taux de présence",  f"{_taux_g}%")
        st.divider()

        for _stat in _att_stats:
            _tx = float(_stat.get("taux_presence") or 0)
            _color = "#10B981" if _tx >= 75 else "#F59E0B" if _tx >= 50 else "#EF4444"
            st.markdown(
                f"**{_stat['course_name']}** — "
                f"<span style='color:{_color};font-weight:700'>{_tx}%</span> présence  "
                f"· {_stat['presences']} présent(s) / {_stat['total_seances']} séance(s)",
                unsafe_allow_html=True
            )
            st.progress(min(_tx / 100, 1.0))


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 7 : MESSAGES
# ══════════════════════════════════════════════════════════════════════════════
with tab_messages:
    st.markdown("#### Messages de mes professeurs")
    try:
        _msgs = ClassMessageQueries.get_by_class(class_id)
    except Exception as _e:
        st.error(str(_e)); _msgs = []

    if not _msgs:
        st.info("Aucun message pour l'instant.")
    else:
        for _m in _msgs:
            _urg = _m.get("is_urgent", False)
            _bg  = "#FEF2F2" if _urg else "#F8FAFC"
            _bd  = "#DC2626" if _urg else "#E2E8F0"
            _ts  = _m["created_at"].strftime("%d/%m/%Y à %H:%M") if _m.get("created_at") else ""
            st.markdown(f"""
            <div style="background:{_bg};border:1px solid {_bd};
                        border-radius:10px;padding:1rem;margin-bottom:0.75rem">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem">
                    <strong>{"🚨 " if _urg else ""}{ _m['subject']}</strong>
                    <span style="font-size:0.78rem;color:#94A3B8">{_ts}</span>
                </div>
                <div style="color:#475569;font-size:0.875rem">
                    👨‍🏫 {_m['professor_name']}
                </div>
                <p style="color:#1E293B;margin:0.5rem 0 0">{_m['body']}</p>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 8 : MON PARCOURS
# ══════════════════════════════════════════════════════════════════════════════
with tab_parcours:
    st.markdown("#### Mon parcours académique")
    st.caption("Historique de vos inscriptions et progression année par année.")
    try:
        _enrollments = AcademicEnrollmentQueries.get_by_student(student["id"])
    except Exception as _e:
        st.error(str(_e)); _enrollments = []

    if not _enrollments:
        st.info("Aucun historique d'inscription disponible. "
                "Contactez l'administration pour mettre à jour votre parcours.")
    else:
        _STATUS_COLORS_STU = {
            "inscrit": "#3B82F6", "admis": "#10B981",
            "redoublant": "#F59E0B", "transfere": "#8B5CF6", "abandonne": "#EF4444",
        }
        _STATUS_LABELS_STU = {
            "inscrit": "Inscrit",  "admis": "Admis(e)",
            "redoublant": "Redoublant(e)", "transfere": "Transféré(e)",
            "abandonne": "Abandonné(e)",
        }
        for _enr in _enrollments:
            _sc = _STATUS_COLORS_STU.get(_enr["status"], "#64748B")
            _sl = _STATUS_LABELS_STU.get(_enr["status"], _enr["status"])
            st.markdown(f"""
            <div style="border-left:4px solid {_sc};padding:0.75rem 1rem;
                        margin-bottom:0.75rem;background:#F8FAFC;border-radius:0 8px 8px 0">
                <div style="font-weight:700;color:#1E293B">{_enr['academic_year']}</div>
                <div style="color:#475569;font-size:0.875rem">
                    🏫 {_enr['class_name']} · 🎓 {_enr['promotion_name']}
                    {f"· 🗂️ {_enr['option_name']}" if _enr.get('option_name') else ''}
                </div>
                <div style="margin-top:0.25rem">
                    <span style="background:{_sc}22;color:{_sc};
                                 font-size:0.78rem;font-weight:600;
                                 padding:0.15rem 0.5rem;border-radius:999px">
                        {_sl}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
