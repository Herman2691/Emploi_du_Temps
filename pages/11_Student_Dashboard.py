# pages/11_Student_Dashboard.py
import streamlit as st
from datetime import datetime, timedelta
from utils.auth import require_student_auth, get_current_student, logout_student, change_student_password
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
tab_edt, tab_tp, tab_notes, tab_cours, tab_bulletin, tab_presence, tab_messages, tab_parcours, tab_progression, tab_frais, tab_fiches, tab_compte = st.tabs([
    "📅 Mon Horaire",
    "📝 Mes TPs",
    "📊 Mes Notes",
    "📚 Cours & Documents",
    "🎓 Mon Bulletin",
    "📍 Mon Assiduité",
    "💬 Messages",
    "📈 Mon Parcours",
    "📈 Progression",
    "💰 Mes Frais",
    "📋 Mes Fiches",
    "⚙️ Mon Compte",
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
        except Exception as _ical_err:
            st.caption(f"⚠️ Export calendrier indisponible : {_ical_err}")

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
                        _sview_key  = f"show_subj_{tp['id']}"
                        _sview_open = st.session_state.get(_sview_key, False)
                        try:
                            _subj_bytes = get_pdf_bytes(tp["subject_url"])
                        except Exception:
                            _subj_bytes = None
                        _subj_name = tp.get("subject_file_name", "sujet.pdf")
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
                            _slbl = "🙈 Fermer" if _sview_open else "👁️ Lire le sujet"
                            if st.button(_slbl, key=f"btn_subj_{tp['id']}",
                                         use_container_width=True):
                                st.session_state[_sview_key] = not _sview_open
                        if _sview_open:
                            if _subj_bytes:
                                try:
                                    import fitz as _fitz_tp
                                    _tp_page_key = f"tp_page_{tp['id']}"
                                    _tp_pdoc     = _fitz_tp.open(stream=_subj_bytes, filetype="pdf")
                                    _tp_total    = len(_tp_pdoc)

                                    _tc1, _tc2, _tc3 = st.columns([1, 2, 1])
                                    _tp_now = st.session_state.get(_tp_page_key, 0)
                                    with _tc1:
                                        if st.button("◀ Précédent",
                                                     key=f"prev_tp_{tp['id']}",
                                                     disabled=(_tp_now == 0),
                                                     use_container_width=True):
                                            st.session_state[_tp_page_key] = _tp_now - 1
                                    with _tc3:
                                        if st.button("Suivant ▶",
                                                     key=f"next_tp_{tp['id']}",
                                                     disabled=(_tp_now >= _tp_total - 1),
                                                     use_container_width=True):
                                            st.session_state[_tp_page_key] = _tp_now + 1

                                    _tp_cur = max(0, min(
                                        st.session_state.get(_tp_page_key, 0), _tp_total - 1
                                    ))
                                    with _tc2:
                                        st.markdown(
                                            f"<div style='text-align:center;padding:0.4rem 0;"
                                            f"color:#64748B;font-size:0.88rem'>"
                                            f"Page {_tp_cur + 1} / {_tp_total}</div>",
                                            unsafe_allow_html=True,
                                        )
                                    _tp_pix = _tp_pdoc[_tp_cur].get_pixmap(
                                        matrix=_fitz_tp.Matrix(2.0, 2.0)
                                    )
                                    _tp_pdoc.close()
                                    st.image(_tp_pix.tobytes("png"), use_container_width=True)

                                except ImportError:
                                    st.info("📥 Utilisez le bouton Télécharger pour lire ce fichier.")
                                except Exception as _e:
                                    st.error(f"Erreur lecture PDF : {_e}")
                            else:
                                st.warning("⚠️ Fichier sujet indisponible sur le serveur.")
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

    # ── Historique de mes réclamations (Point 11) ────────────────────────────
    st.divider()
    st.markdown("#### 📋 Mes réclamations")
    try:
        _my_claims = GradeClaimQueries.get_by_student(student["id"]) or []
    except Exception as _mce:
        st.error(str(_mce)); _my_claims = []

    if not _my_claims:
        st.info("Vous n'avez déposé aucune réclamation.")
    else:
        _ST_ICON = {
            "pending":  "⏳",
            "accepted": "✅",
            "rejected": "❌",
        }
        _ST_LBL = {
            "pending":  "En attente",
            "accepted": "Acceptée",
            "rejected": "Rejetée",
        }
        _DEPT_LBL = {
            True:  "✔️ Validée par le département",
            False: "❌ Refusée par le département",
            None:  "⏳ En attente de validation département",
        }
        for _mc in _my_claims:
            _st_icon = _ST_ICON.get(_mc.get("status",""), "❓")
            _st_lbl  = _ST_LBL.get(_mc.get("status",""), _mc.get("status","—"))
            _cr_at   = _mc.get("created_at")
            _cr_str  = _cr_at.strftime("%d/%m/%Y %H:%M") if _cr_at else "—"
            with st.expander(
                f"{_st_icon} {_mc.get('course_name','—')} · "
                f"{_mc.get('exam_type','—')} · {_mc.get('session_name','—')} "
                f"— {_st_lbl} (déposée le {_cr_str})"
            ):
                st.markdown(
                    f"**Note :** {_mc.get('grade','—')}/{_mc.get('max_grade','—')}  \n"
                    f"**Votre motif :** {_mc.get('reason','—')}"
                )
                if _mc.get("status") != "pending":
                    _rev_at  = _mc.get("reviewed_at")
                    _rev_str = _rev_at.strftime("%d/%m/%Y %H:%M") if _rev_at else "—"
                    st.markdown(
                        f"**Réponse du professeur :** "
                        f"{_mc.get('professor_response') or '—'}  \n"
                        f"*Traitée le {_rev_str}*"
                    )
                    _dv = _mc.get("dept_validated")
                    st.info(_DEPT_LBL.get(_dv, "—"))
                    if _mc.get("dept_notes"):
                        st.caption(f"Note du département : {_mc['dept_notes']}")

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 : COURS & DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_cours:
    from db.queries import CourseQueries as _CQ_stu

    _sub_prog, _sub_docs = st.tabs(["📋 Mon Programme", "📄 Documents de cours"])

    # ── Sous-onglet A : Programme structuré par session ──────────────────────
    with _sub_prog:
        try:
            _programme = _CQ_stu.get_programme_by_class(class_id)
        except Exception as _e_prog:
            st.error(str(_e_prog))
            _programme = []

        if not _programme:
            st.info("📭 Aucun cours enregistré pour votre classe.")
        else:
            # Mapping group_label → libellé affiché (ordre trié → Session 1 en premier)
            _SESSION_LABELS = {}
            _sorted_groups = sorted(set(
                _c.get("ue_group") or "—" for _c in _programme
            ))
            for _i, _g in enumerate(_sorted_groups):
                _SESSION_LABELS[_g] = f"Session {_i + 1}"

            # Grouper : groupe → UE → cours
            _groups = {}
            for _c in _programme:
                _grp = _c.get("ue_group") or "—"
                _ue_id = _c.get("ue_id")
                _ue_key = (_ue_id, _c.get("ue_code") or "", _c.get("ue_name") or "",
                           float(_c.get("ue_credits") or 0))
                _groups.setdefault(_grp, {}).setdefault(_ue_key, []).append(_c)

            _TH_SESSION = ("padding:10px 14px;background:#1E40AF;color:white;"
                           "font-size:0.9rem;font-weight:700;text-align:center;"
                           "letter-spacing:0.05em;border:1px solid #1E40AF")
            _TH = ("padding:7px 10px;border:1px solid #CBD5E1;"
                   "background:#2563EB;color:white;font-size:0.78rem;text-align:center")
            _TR_UE = ("padding:6px 10px;border:1px solid #CBD5E1;"
                      "background:#EFF6FF;font-weight:600;font-size:0.83rem;color:#1E3A8A")
            _TR_EC = ("padding:5px 10px;border:1px solid #E2E8F0;"
                      "background:#F8FAFC;font-size:0.78rem;color:#475569")

            for _grp_label in sorted(_groups.keys()):
                _ue_map = _groups[_grp_label]
                _session_title = _SESSION_LABELS.get(_grp_label, _grp_label).upper()

                _rows_html = ""
                for (_ue_id, _ue_code, _ue_name, _ue_cred), _courses in sorted(
                    _ue_map.items(), key=lambda x: (x[0][1], x[0][2])
                ):
                    if _ue_id:
                        _rows_html += (
                            f"<tr>"
                            f"<td style='{_TR_UE};text-align:center'>{_ue_code or '—'}</td>"
                            f"<td style='{_TR_UE}'>{_ue_name}</td>"
                            f"<td style='{_TR_UE};text-align:center'>—</td>"
                            f"<td style='{_TR_UE};text-align:center'>"
                            f"{int(_ue_cred) if _ue_cred else '—'}</td>"
                            f"<td style='{_TR_UE}'>—</td>"
                            f"</tr>"
                        )
                        for _ec in _courses:
                            _ec_cred = _ec.get("credits_ec")
                            _rows_html += (
                                f"<tr>"
                                f"<td style='{_TR_EC};text-align:center'>—</td>"
                                f"<td style='{_TR_EC};padding-left:2rem'>↳ {_ec['name']}</td>"
                                f"<td style='{_TR_EC};text-align:center'>"
                                f"{int(_ec_cred) if _ec_cred else '—'}</td>"
                                f"<td style='{_TR_EC};text-align:center'>—</td>"
                                f"<td style='{_TR_EC}'>{_ec.get('professor_name') or '—'}</td>"
                                f"</tr>"
                            )
                    else:
                        for _ec in _courses:
                            _ec_cred = _ec.get("credits_ec")
                            _rows_html += (
                                f"<tr>"
                                f"<td style='{_TR_EC};text-align:center'>—</td>"
                                f"<td style='{_TR_EC}'>{_ec['name']}</td>"
                                f"<td style='{_TR_EC};text-align:center'>"
                                f"{int(_ec_cred) if _ec_cred else '—'}</td>"
                                f"<td style='{_TR_EC};text-align:center'>—</td>"
                                f"<td style='{_TR_EC}'>{_ec.get('professor_name') or '—'}</td>"
                                f"</tr>"
                            )

                st.markdown(
                    f"""<div style="overflow-x:auto;margin-bottom:2rem">
                    <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
                        <thead>
                            <tr>
                                <td colspan="5" style="{_TH_SESSION}">
                                    UE DU {_session_title}
                                </td>
                            </tr>
                            <tr>
                                <th style="{_TH};width:90px">Code UE</th>
                                <th style="{_TH}">Intitulés UE / EC</th>
                                <th style="{_TH};width:85px">Crédits EC</th>
                                <th style="{_TH};width:85px">Crédits UE</th>
                                <th style="{_TH}">Professeur titulaire</th>
                            </tr>
                        </thead>
                        <tbody>{_rows_html}</tbody>
                    </table></div>""",
                    unsafe_allow_html=True,
                )

    # ── Sous-onglet B : Documents PDF ─────────────────────────────────────────
    with _sub_docs:
        try:
            docs = CourseDocumentQueries.get_by_class(class_id)
        except Exception as e:
            st.error(str(e))
            docs = []

        if not docs:
            st.info("📭 Aucun document de cours disponible pour l'instant.")
        else:
            by_course = {}
            for d in docs:
                cn = d["course_name"]
                by_course.setdefault(cn, []).append(d)

            for course_name, course_docs in by_course.items():
                st.markdown(f"#### 📘 {course_name}")
                for doc in course_docs:
                    _state_key = f"show_doc_{doc['id']}"
                    _is_open   = st.session_state.get(_state_key, False)
                    with st.expander(
                        f"📄 {doc['title']} — 👨‍🏫 {doc['professor_name']}",
                        expanded=_is_open,
                    ):
                        st.caption(
                            f"📄 {doc['file_name']} · "
                            f"💾 {doc.get('file_size_kb', 0)} Ko"
                        )
                        if doc.get("description"):
                            st.caption(doc["description"])

                        try:
                            _pdf_bytes = get_pdf_bytes(doc["file_url"]) if doc.get("file_url") else None
                        except Exception:
                            _pdf_bytes = None

                        col_view, col_dl, _ = st.columns([1, 1, 3])
                        with col_view:
                            _btn_label = "🙈 Fermer" if _is_open else "👁️ Lire"
                            if st.button(_btn_label, key=f"btn_view_{doc['id']}",
                                         use_container_width=True):
                                st.session_state[_state_key] = not _is_open
                                if _is_open:
                                    st.session_state.pop(f"pdf_page_{doc['id']}", None)
                        with col_dl:
                            if _pdf_bytes:
                                st.download_button(
                                    "⬇️ Télécharger", _pdf_bytes,
                                    file_name=doc["file_name"],
                                    mime="application/pdf",
                                    key=f"dl_doc_{doc['id']}",
                                    use_container_width=True,
                                )
                            else:
                                st.caption("Fichier indisponible")

                        if _is_open:
                            if _pdf_bytes:
                                try:
                                    import fitz as _fitz
                                    _page_key = f"pdf_page_{doc['id']}"
                                    _pdoc     = _fitz.open(stream=_pdf_bytes, filetype="pdf")
                                    _total_pg = len(_pdoc)

                                    _nc1, _nc2, _nc3 = st.columns([1, 2, 1])
                                    _pg_now = st.session_state.get(_page_key, 0)
                                    with _nc1:
                                        if st.button("◀ Précédent",
                                                     key=f"prev_pg_{doc['id']}",
                                                     disabled=(_pg_now == 0),
                                                     use_container_width=True):
                                            st.session_state[_page_key] = _pg_now - 1
                                    with _nc3:
                                        if st.button("Suivant ▶",
                                                     key=f"next_pg_{doc['id']}",
                                                     disabled=(_pg_now >= _total_pg - 1),
                                                     use_container_width=True):
                                            st.session_state[_page_key] = _pg_now + 1

                                    _cur_pg = max(0, min(
                                        st.session_state.get(_page_key, 0), _total_pg - 1
                                    ))
                                    with _nc2:
                                        st.markdown(
                                            f"<div style='text-align:center;padding:0.4rem 0;"
                                            f"color:#64748B;font-size:0.88rem'>"
                                            f"Page {_cur_pg + 1} / {_total_pg}</div>",
                                            unsafe_allow_html=True,
                                        )

                                    _pix = _pdoc[_cur_pg].get_pixmap(
                                        matrix=_fitz.Matrix(2.0, 2.0)
                                    )
                                    _pdoc.close()
                                    st.image(_pix.tobytes("png"), use_container_width=True)

                                except ImportError:
                                    st.info("📥 Utilisez le bouton Télécharger pour lire ce fichier.")
                                except Exception as _e:
                                    st.error(f"Erreur lecture PDF : {_e}")
                            else:
                                st.warning(
                                    "⚠️ Fichier indisponible. "
                                    "Demandez au professeur de le re-uploader."
                                )
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 5 : MON BULLETIN
# ══════════════════════════════════════════════════════════════════════════════
with tab_bulletin:
    from db.queries import DeliberationAnnuelleQueries as _DAQ_stu

    try:
        pub_sessions = GradeQueries.get_published_sessions_by_student(student["id"])
    except Exception as e:
        st.error(str(e)); pub_sessions = []

    try:
        _pub_delib_years = _DAQ_stu.get_published_years_by_student(student["id"]) or []
    except Exception:
        _pub_delib_years = []

    _SESSION_LABEL_DELIB = "📋 Délibération annuelle"
    session_choices = [s["session_name"] for s in (pub_sessions or [])]
    if _pub_delib_years:
        session_choices = [_SESSION_LABEL_DELIB] + session_choices

    if not session_choices:
        st.info(
            "Aucun bulletin publié pour l'instant. "
            "Les résultats apparaîtront ici une fois que votre département les aura publiés."
        )
    else:
        selected_session = st.selectbox(
            "Sélectionner une session", options=session_choices,
            key="bulletin_session_sel"
        )

        # ── VUE DÉLIBÉRATION ANNUELLE ─────────────────────────────────────────
        if selected_session == _SESSION_LABEL_DELIB:
            _delib_year_choices = [r["academic_year"] for r in _pub_delib_years]
            _sel_delib_yr = st.selectbox(
                "Année académique", options=_delib_year_choices,
                key="delib_yr_stu"
            )
            if _sel_delib_yr:
                try:
                    _delib = _DAQ_stu.get_by_student_year(student["id"], _sel_delib_yr)
                except Exception as _e_d:
                    st.error(str(_e_d)); _delib = None

                if not _delib:
                    st.info("Aucune délibération annuelle disponible.")
                else:
                    _dec     = _delib.get("decision","en_cours")
                    _dec_cfg = {
                        "admis":      ("✅ Admis(e)",      "#059669","#D1FAE5"),
                        "redoublant": ("🔄 Redoublant(e)", "#D97706","#FEF3C7"),
                        "en_cours":   ("⏳ En cours",      "#64748B","#F1F5F9"),
                    }
                    _dec_lbl, _dec_clr, _dec_bg = _dec_cfg.get(_dec, _dec_cfg["en_cours"])

                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,{_dec_clr}22,{_dec_clr}11);
                                border:1px solid {_dec_clr}44;border-radius:12px;
                                padding:1rem 1.5rem;margin-bottom:1rem">
                        <div style="font-size:0.85rem;color:#64748B;margin-bottom:0.5rem">
                            Délibération annuelle · <strong>{_sel_delib_yr}</strong>
                        </div>
                        <div style="display:flex;gap:2rem;align-items:center;flex-wrap:wrap">
                            <div>
                                <div style="font-size:0.75rem;color:#94A3B8">Moyenne annuelle</div>
                                <div style="font-size:2rem;font-weight:700;color:{_dec_clr}">
                                    {float(_delib['moy_annuelle'] or 0):.2f}
                                    <span style="font-size:1rem;color:#94A3B8">/20</span>
                                </div>
                            </div>
                            <div>
                                <div style="font-size:0.75rem;color:#94A3B8">Crédits validés</div>
                                <div style="font-size:1.5rem;font-weight:600;color:{_dec_clr}">
                                    {_delib['credits_obtenus']} / {_delib['credits_total']}
                                </div>
                            </div>
                            <div style="margin-left:auto">
                                <div style="font-size:0.75rem;color:#94A3B8">Décision</div>
                                <div style="background:{_dec_bg};color:{_dec_clr};
                                            padding:6px 18px;border-radius:20px;
                                            font-weight:700;font-size:1rem;
                                            display:inline-block;margin-top:4px">
                                    {_dec_lbl}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    _c1d, _c2d = st.columns(2)
                    if _delib.get("moy_s1") is not None:
                        _c1d.metric("Moyenne S1", f"{float(_delib['moy_s1']):.2f}/20")
                    if _delib.get("moy_s2") is not None:
                        _c2d.metric("Moyenne S2", f"{float(_delib['moy_s2']):.2f}/20")

                    if _delib.get("ecs_a_reprendre"):
                        st.warning(
                            f"**ECs à reprendre :** {_delib['ecs_a_reprendre']}"
                        )
                    else:
                        st.success("Tous les ECs validés ✅")

        elif selected_session:
            try:
                bulletin_grades = GradeQueries.get_bulletin_by_student(
                    student["id"], selected_session
                )
            except Exception as e:
                st.error(str(e)); bulletin_grades = []

            if not bulletin_grades:
                st.info("Aucune note disponible pour cette session.")
            else:
                _has_ue_struct = any(g.get("ue_id") for g in bulletin_grades)

                # ══════════════════════════════════════════════════════════════
                # MODE UE/EC — format bulletin académique structuré
                # ══════════════════════════════════════════════════════════════
                if _has_ue_struct:
                    from collections import defaultdict as _ddict

                    # ── Construire ue_map et no_ue_courses ────────────────────
                    ue_map = {}
                    no_ue_courses = {}
                    for g in bulletin_grades:
                        norm = (float(g["grade"]) / float(g["max_grade"]) * 20
                                if g.get("max_grade") else 0.0)
                        if g.get("ue_id"):
                            uk = g["ue_id"]
                            if uk not in ue_map:
                                ue_map[uk] = {
                                    "ue_id":      g["ue_id"],
                                    "ue_name":    g.get("ue_name", ""),
                                    "ue_code":    g.get("ue_code", ""),
                                    "ue_credits": float(g.get("ue_credits") or 0),
                                    "ue_group":   g.get("ue_group", "A"),
                                    "courses":    {},
                                }
                            cn = g["course_name"]
                            if cn not in ue_map[uk]["courses"]:
                                ue_map[uk]["courses"][cn] = {
                                    "credits_ec": float(g.get("credits_ec") or 1),
                                    "exams": [],
                                }
                            ue_map[uk]["courses"][cn]["exams"].append({
                                "type":  g["exam_type"],
                                "grade": float(g["grade"] or 0),
                                "max":   float(g["max_grade"] or 20),
                                "norm":  norm,
                                "comment": g.get("comment"),
                                "prof":    g.get("professor_name", "—"),
                            })
                        else:
                            cn = g["course_name"]
                            if cn not in no_ue_courses:
                                no_ue_courses[cn] = {
                                    "weight": float(g.get("course_weight") or 1),
                                    "exams": [],
                                }
                            no_ue_courses[cn]["exams"].append({
                                "type":  g["exam_type"],
                                "grade": float(g["grade"] or 0),
                                "max":   float(g["max_grade"] or 20),
                                "norm":  norm,
                                "comment": g.get("comment"),
                                "prof":    g.get("professor_name", "—"),
                            })

                    # ── Calculs UE ────────────────────────────────────────────
                    for ue in ue_map.values():
                        for ec in ue["courses"].values():
                            exams = ec["exams"]
                            ec["avg20"] = (sum(e["norm"] for e in exams) / len(exams)
                                           if exams else 0.0)
                        total_cred = sum(ec["credits_ec"] for ec in ue["courses"].values())
                        ue["note_ue"] = (
                            sum(ec["avg20"] * ec["credits_ec"]
                                for ec in ue["courses"].values()) / total_cred
                            if total_cred > 0 else 0.0
                        )
                        ue["decision"]         = "V" if ue["note_ue"] >= 10.0 else "NV"
                        ue["credits_obtained"] = ue["ue_credits"] if ue["decision"] == "V" else 0.0

                    # ── Groupes ───────────────────────────────────────────────
                    by_group = _ddict(list)
                    for ue in ue_map.values():
                        by_group[ue["ue_group"]].append(ue)

                    group_avgs = {}
                    for glabel, ues in by_group.items():
                        total_uc = sum(u["ue_credits"] for u in ues)
                        group_avgs[glabel] = (
                            sum(u["note_ue"] * u["ue_credits"] for u in ues) / total_uc
                            if total_uc > 0 else 0.0
                        )

                    total_ue_credits  = sum(u["ue_credits"] for u in ue_map.values())
                    obtained_credits  = sum(u["credits_obtained"] for u in ue_map.values())
                    total_avg = (
                        sum(u["note_ue"] * u["ue_credits"] for u in ue_map.values())
                        / total_ue_credits if total_ue_credits > 0 else 0.0
                    )
                    all_validated  = all(u["decision"] == "V" for u in ue_map.values())
                    final_decision = "VAL" if all_validated else "NVAL"
                    ecs_a_reprendre = sum(
                        1 for ue in ue_map.values()
                        for ec in ue["courses"].values()
                        if ec["avg20"] < 10.0
                    )

                    # ── Rang & décision officielle ────────────────────────────
                    try:
                        rank_val = GradeQueries.get_class_rank(
                            student["id"], class_id, selected_session)
                    except Exception:
                        rank_val = None
                    try:
                        _dec_row    = StudentResultsQueries.get_by_student_session(
                            student["id"], selected_session)
                        _decision_val = _dec_row.get("decision") if _dec_row else None
                    except Exception:
                        _decision_val = None

                    # ── En-tête ───────────────────────────────────────────────
                    men_label = _mention_label(total_avg)
                    men_color = _mention_color(total_avg)
                    _DEC_CFG  = {
                        "Admis":     ("✅", "#059669", "#D1FAE5"),
                        "Session 2": ("⚠️", "#D97706", "#FEF3C7"),
                        "Ajourné":   ("❌", "#DC2626", "#FEE2E2"),
                    }
                    _dec_icon, _dec_clr, _dec_bg = _DEC_CFG.get(
                        _decision_val, ("", "#64748B", "#F1F5F9"))
                    _decision_html = (
                        f"<div style='margin-left:auto'>"
                        f"<div style='font-size:0.75rem;color:#94A3B8'>Décision officielle</div>"
                        f"<div style='background:{_dec_bg};color:{_dec_clr};"
                        f"padding:4px 14px;border-radius:20px;font-weight:700;"
                        f"font-size:1rem;display:inline-block;margin-top:2px'>"
                        f"{_dec_icon} {_decision_val}</div></div>"
                    ) if _decision_val else ""
                    rank_html = (
                        f"<div><div style='font-size:0.75rem;color:#94A3B8'>Rang</div>"
                        f"<div style='font-size:1.2rem;font-weight:600;color:#1E293B'>"
                        f"{rank_val}</div></div>"
                    ) if rank_val is not None else ""

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
                                    {total_avg:.2f}
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

                    # ── Tableau UE/EC ─────────────────────────────────────────
                    _S_TH  = ("padding:6px 8px;border:1px solid #CBD5E1;"
                               "background:#1E40AF;color:white;font-size:0.78rem;text-align:center")
                    _S_UE  = ("padding:5px 8px;border:1px solid #CBD5E1;"
                               "background:#EFF6FF;font-weight:600;font-size:0.82rem")
                    _S_EC  = ("padding:4px 8px;border:1px solid #E2E8F0;"
                               "background:#F8FAFC;font-size:0.78rem;color:#475569")
                    _S_SUM = ("padding:6px 8px;border:1px solid #CBD5E1;"
                               "background:#F1F5F9;font-weight:600;font-size:0.8rem")

                    rows_html = ""
                    for glabel in sorted(by_group.keys()):
                        ues_g = sorted(by_group[glabel], key=lambda u: u.get("ue_code", ""))
                        for ue in ues_g:
                            nue   = ue["note_ue"]
                            dec   = ue["decision"]
                            nc    = "#059669" if nue >= 10 else "#DC2626"
                            dc    = "#059669" if dec == "V" else "#DC2626"
                            rows_html += (
                                f"<tr>"
                                f"<td style='{_S_UE};text-align:center'>{ue['ue_code'] or ''}</td>"
                                f"<td style='{_S_UE}'>{ue['ue_name']}</td>"
                                f"<td style='{_S_UE};text-align:center'>—</td>"
                                f"<td style='{_S_UE};text-align:center'>{ue['ue_credits']:.0f}</td>"
                                f"<td style='{_S_UE};text-align:center'>—</td>"
                                f"<td style='{_S_UE};text-align:center;color:{nc}'>{nue:.2f}</td>"
                                f"<td style='{_S_UE};text-align:center;color:{dc};font-weight:700'>{dec}</td>"
                                f"</tr>"
                            )
                            for cn, ec in sorted(ue["courses"].items()):
                                ne  = ec["avg20"]
                                nce = "#059669" if ne >= 10 else "#DC2626"
                                rows_html += (
                                    f"<tr>"
                                    f"<td style='{_S_EC};text-align:center'>—</td>"
                                    f"<td style='{_S_EC};padding-left:1.8rem'>↳ {cn}</td>"
                                    f"<td style='{_S_EC};text-align:center'>{ec['credits_ec']:.0f}</td>"
                                    f"<td style='{_S_EC};text-align:center'>—</td>"
                                    f"<td style='{_S_EC};text-align:center;color:{nce}'>{ne:.2f}</td>"
                                    f"<td style='{_S_EC};text-align:center'>—</td>"
                                    f"<td style='{_S_EC};text-align:center'>—</td>"
                                    f"</tr>"
                                )

                    sum_rows = ""
                    for glabel in sorted(by_group.keys()):
                        gavg  = group_avgs.get(glabel, 0)
                        gc    = "#059669" if gavg >= 10 else "#DC2626"
                        sum_rows += (
                            f"<tr>"
                            f"<td colspan='5' style='{_S_SUM};text-align:right'>"
                            f"Moyenne Groupe {glabel} :</td>"
                            f"<td style='{_S_SUM};text-align:center;color:{gc}'>{gavg:.2f}</td>"
                            f"<td style='{_S_SUM}'></td>"
                            f"</tr>"
                        )
                    _fc  = "#059669" if final_decision == "VAL" else "#DC2626"
                    _tac = "#059669" if total_avg >= 10 else "#DC2626"
                    sum_rows += (
                        f"<tr>"
                        f"<td colspan='2' style='{_S_SUM}'>Moyenne Totale</td>"
                        f"<td style='{_S_SUM};text-align:center'>{ecs_a_reprendre} EC à reprendre</td>"
                        f"<td style='{_S_SUM};text-align:center'>{obtained_credits:.0f}/{total_ue_credits:.0f} crédits</td>"
                        f"<td style='{_S_SUM}'></td>"
                        f"<td style='{_S_SUM};text-align:center;color:{_tac}'>{total_avg:.2f}</td>"
                        f"<td style='{_S_SUM};text-align:center;color:{_fc};font-size:1rem'>{final_decision}</td>"
                        f"</tr>"
                    )

                    st.markdown(
                        f"""<div style="overflow-x:auto;margin:1rem 0">
                        <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
                            <thead><tr>
                                <th style="{_S_TH};width:70px">Code UE</th>
                                <th style="{_S_TH}">Intitulés UE / EC</th>
                                <th style="{_S_TH};width:70px">Crédits EC</th>
                                <th style="{_S_TH};width:70px">Crédits UE</th>
                                <th style="{_S_TH};width:80px">Note EC /20</th>
                                <th style="{_S_TH};width:80px">Note UE /20</th>
                                <th style="{_S_TH};width:70px">Décision</th>
                            </tr></thead>
                            <tbody>{rows_html}{sum_rows}</tbody>
                        </table></div>""",
                        unsafe_allow_html=True,
                    )

                    # ── Export PDF UE ─────────────────────────────────────────
                    st.divider()
                    try:
                        from utils.pdf_export import generate_bulletin_pdf_ue
                        from db.queries import ClassQueries as _ClsQ
                        _cls_info = _ClsQ.get_by_id(class_id)
                        _pdf_bul  = generate_bulletin_pdf_ue(
                            student_name=_display_name,
                            student_number=student["student_number"],
                            class_name=_cls_info["name"] if _cls_info else "—",
                            promotion_name=_cls_info.get("promotion_name","—") if _cls_info else "—",
                            university_name=_cls_info.get("university_name","UniSchedule") if _cls_info else "UniSchedule",
                            session_name=selected_session,
                            ue_map=ue_map,
                            by_group=dict(by_group),
                            group_avgs=group_avgs,
                            total_avg=total_avg,
                            obtained_credits=obtained_credits,
                            total_ue_credits=total_ue_credits,
                            ecs_a_reprendre=ecs_a_reprendre,
                            final_decision=final_decision,
                            mention=men_label,
                            rank=rank_val,
                            faculty_name=_cls_info.get("faculty_name","") if _cls_info else "",
                            department_name=_cls_info.get("department_name","") if _cls_info else "",
                        )
                        st.download_button(
                            "📄 Télécharger le bulletin PDF (format UE)",
                            data=_pdf_bul,
                            file_name=f"bulletin_ue_{student['student_number']}_{selected_session}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary",
                        )
                    except Exception as _e:
                        st.caption(f"Export PDF indisponible : {_e}")

                # ══════════════════════════════════════════════════════════════
                # MODE PAR COURS — affichage classique (pas de structure UE)
                # ══════════════════════════════════════════════════════════════
                else:
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
                            "max":   g["max_grade"],
                            "norm":  norm,
                            "comment": g.get("comment"),
                            "prof":    g.get("professor_name", "—"),
                        })

                    for cn, data in by_course_b.items():
                        exs = data["exams"]
                        data["avg20"] = sum(e["norm"] for e in exs) / len(exs)

                    total_w_b   = sum(d["weight"] for d in by_course_b.values())
                    overall_avg = (
                        sum(d["avg20"] * d["weight"] for d in by_course_b.values())
                        / total_w_b if total_w_b > 0 else 0.0
                    )

                    try:
                        rank_val = GradeQueries.get_class_rank(
                            student["id"], class_id, selected_session)
                    except Exception:
                        rank_val = None

                    men_label = _mention_label(overall_avg)
                    men_color = _mention_color(overall_avg)
                    rank_html = (
                        f"<div><div style='font-size:0.75rem;color:#94A3B8'>Rang</div>"
                        f"<div style='font-size:1.2rem;font-weight:600;color:#1E293B'>"
                        f"{rank_val}</div></div>"
                        if rank_val is not None else ""
                    )

                    try:
                        _dec_row = StudentResultsQueries.get_by_student_session(
                            student["id"], selected_session)
                        _decision_val = _dec_row.get("decision") if _dec_row else None
                    except Exception:
                        _decision_val = None

                    _DEC_CFG = {
                        "Admis":     ("✅", "#059669", "#D1FAE5"),
                        "Session 2": ("⚠️", "#D97706", "#FEF3C7"),
                        "Ajourné":   ("❌", "#DC2626", "#FEE2E2"),
                    }
                    _dec_icon, _dec_clr, _dec_bg = _DEC_CFG.get(
                        _decision_val, ("", "#64748B", "#F1F5F9"))
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

                    st.divider()
                    try:
                        from utils.pdf_export import generate_bulletin_pdf
                        from db.queries import ClassQueries as _ClsQ
                        _cls_info = _ClsQ.get_by_id(class_id)
                        _pdf_bul  = generate_bulletin_pdf(
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


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 9 : PROGRESSION
# ══════════════════════════════════════════════════════════════════════════════
with tab_progression:
    import pandas as _pd_prog
    from db.queries import DeliberationAnnuelleQueries as _DAQ_prog
    from db.connection import execute_query as _eq_prog

    st.markdown("#### 📈 Mon parcours académique")

    # ── 1. Délibérations annuelles publiées ────────────────────────────────────
    _annual_rows = []
    try:
        _pub_years_prog = _DAQ_prog.get_published_years_by_student(student["id"]) or []
        for _yr_row in _pub_years_prog:
            _yr = _yr_row["academic_year"]
            _d  = _DAQ_prog.get_by_student_year(student["id"], _yr)
            if _d:
                _annual_rows.append({
                    "Année":            _yr,
                    "Moy S1":           float(_d["moy_s1"]) if _d.get("moy_s1") is not None else None,
                    "Moy S2":           float(_d["moy_s2"]) if _d.get("moy_s2") is not None else None,
                    "Moy Annuelle":     float(_d["moy_annuelle"]) if _d.get("moy_annuelle") is not None else None,
                    "Crédits validés":  f"{_d.get('credits_obtenus',0)}/{_d.get('credits_total',0)}",
                    "Décision":         _d.get("decision","—"),
                })
    except Exception as _e_prog:
        st.warning(f"Impossible de charger les délibérations annuelles : {_e_prog}")

    # ── 2. Résultats par session ───────────────────────────────────────────────
    _session_rows = []
    try:
        _session_rows = _eq_prog(
            """SELECT academic_year, session_name, average, decision, rank
               FROM student_session_results
               WHERE student_id = %s ORDER BY academic_year, session_name""",
            (student["id"],),
            fetch="all",
        ) or []
    except Exception:
        _session_rows = []

    # ── Affichage ──────────────────────────────────────────────────────────────
    _has_annual  = len(_annual_rows) > 0
    _has_session = len(_session_rows) > 0

    if not _has_annual and not _has_session:
        st.info("Aucun historique académique disponible pour l'instant.")
    else:
        if _has_annual:
            st.markdown("##### Bilan annuel")
            _df_annual = _pd_prog.DataFrame(_annual_rows)
            st.dataframe(_df_annual, use_container_width=True, hide_index=True)

            # Graphique des moyennes annuelles
            _chart_data = _df_annual[["Année","Moy Annuelle"]].dropna(subset=["Moy Annuelle"])
            if not _chart_data.empty:
                st.line_chart(
                    _chart_data.set_index("Année"),
                    use_container_width=True,
                )

        if _has_session:
            st.markdown("##### Résultats par session")
            _df_sess = _pd_prog.DataFrame([{
                "Année":      r["academic_year"],
                "Session":    r["session_name"],
                "Moyenne":    float(r["average"]) if r.get("average") is not None else None,
                "Rang":       r.get("rank"),
                "Décision":   r.get("decision","—"),
            } for r in _session_rows])
            st.dataframe(_df_sess, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# UNIBOT — BULLE FLOTTANTE
# ══════════════════════════════════════════════════════════════════════════════
from utils.chatbot import render_floating_chatbot, _system_student
try:
    _cb_grades = GradeQueries.get_by_student(student["id"]) or []
except Exception:
    _cb_grades = []
try:
    _cb_sched = ScheduleQueries.get_by_class(class_id) or []
except Exception:
    _cb_sched = []
try:
    _cb_claims = GradeClaimQueries.get_by_student(student["id"]) or []
except Exception:
    _cb_claims = []
try:
    _cb_results = StudentResultsQueries.get_by_student(student["id"]) or []
except Exception:
    _cb_results = []
_cb_system = _system_student(student, _cb_grades, _cb_sched, _cb_claims, _cb_results)
render_floating_chatbot(_cb_system, session_key="chatbot_student")

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET : MES FRAIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_frais:
    from db.queries import StudentFeeQueries as _SFQ_stu

    try:
        _my_fees = _SFQ_stu.get_by_student(student["id"])
    except Exception as _ef:
        st.error(str(_ef))
        _my_fees = []

    if not _my_fees:
        st.info("💰 Aucun frais académique enregistré pour votre compte pour l'instant.")
    else:
        # Résumé
        _total_fees  = len(_my_fees)
        _paid_fees   = sum(1 for f in _my_fees if f["is_paid"])
        _unpaid_fees = _total_fees - _paid_fees
        _total_amt   = sum(float(f.get("montant") or 0) for f in _my_fees)
        _paid_amt    = sum(float(f.get("montant") or 0) for f in _my_fees if f["is_paid"])
        _unpaid_amt  = _total_amt - _paid_amt

        _currency = _my_fees[0]["currency"] if _my_fees else "$"

        _m1, _m2, _m3 = st.columns(3)
        _m1.metric("Total frais", f"{_total_amt:.0f} {_currency}")
        _m2.metric("Payé", f"{_paid_amt:.0f} {_currency}")
        _m3.metric("Restant dû", f"{_unpaid_amt:.0f} {_currency}")
        st.divider()

        # Tableau style document de référence
        _TH_F = ("padding:8px 12px;border:1px solid #CBD5E1;"
                 "background:#1E40AF;color:white;font-size:0.8rem;text-align:left")
        _TD_F  = "padding:7px 12px;border:1px solid #E2E8F0;font-size:0.83rem"

        _rows_f = ""
        for _fee in _my_fees:
            _mand = " <span style='color:#6B7280;font-size:0.73rem'>(Obligé)</span>" \
                    if _fee.get("is_mandatory") else ""
            _yr   = f" <span style='color:#94A3B8;font-size:0.73rem'>{_fee['academic_year']}</span>" \
                    if _fee.get("academic_year") else ""
            _amt  = f"{float(_fee['montant']):.0f} {_fee['currency']}" \
                    if _fee.get("montant") else "#"
            if _fee["is_paid"]:
                _badge = ("<span style='background:#D1FAE5;color:#065F46;"
                          "padding:3px 14px;border-radius:999px;font-size:0.78rem;"
                          "font-weight:600'>Payé</span>")
            else:
                _badge = ("<span style='background:#FEE2E2;color:#991B1B;"
                          "padding:3px 14px;border-radius:999px;font-size:0.78rem;"
                          "font-weight:600'>Non</span>")
            _rows_f += (
                f"<tr>"
                f"<td style='{_TD_F}'>{_fee['fee_name']}{_mand}{_yr}</td>"
                f"<td style='{_TD_F};text-align:center'>{_amt}</td>"
                f"<td style='{_TD_F};text-align:center'>{_badge}</td>"
                f"</tr>"
            )

        st.markdown(
            f"""<div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
                <thead><tr>
                    <th style="{_TH_F}">Intitulé</th>
                    <th style="{_TH_F};text-align:center;width:120px">Prix</th>
                    <th style="{_TH_F};text-align:center;width:120px">Statut</th>
                </tr></thead>
                <tbody>{_rows_f}</tbody>
            </table></div>""",
            unsafe_allow_html=True
        )

        if _unpaid_fees > 0:
            st.warning(
                f"Vous avez **{_unpaid_fees}** frais non payé(s) "
                f"pour un total de **{_unpaid_amt:.0f} {_currency}**. "
                "Veuillez vous rapprocher de l'administration."
            )


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET : MES FICHES D'ENRÔLEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_fiches:
    from utils.pdf_export import generate_enrollment_pdf, generate_attendance_report_pdf
    from db.queries import (CourseQueries as _CQ_fiche, ClassQueries as _ClsQ_fiche,
                            AttendanceQueries as _AttQ_fiche, AcademicYearQueries as _AYQ_fiche)

    # Charger les infos de classe et le programme une seule fois
    try:
        _cls_fiche   = _ClsQ_fiche.get_by_id(class_id)
        _prog_fiche  = _CQ_fiche.get_programme_by_class(class_id)
        _att_fiche   = _AttQ_fiche.get_student_stats(student["id"], class_id) or []
    except Exception as _ef2:
        st.error(str(_ef2))
        _cls_fiche = None
        _prog_fiche = []
        _att_fiche  = []

    # Année académique courante
    try:
        _uni_id_fiche = student.get("university_id")
        _ay_fiche = _AYQ_fiche.get_current(_uni_id_fiche) if _uni_id_fiche else None
        _ay_label_fiche = _ay_fiche["label"] if _ay_fiche else ""
    except Exception:
        _ay_label_fiche = ""

    _fac_name  = (_cls_fiche.get("faculty_name", "")     if _cls_fiche else "")
    _dept_name = (_cls_fiche.get("department_name", "")  if _cls_fiche else "")
    _promo_name= (_cls_fiche.get("promotion_name", "")   if _cls_fiche else "")
    _uni_name  = (_cls_fiche.get("university_name", "UniSchedule") if _cls_fiche else "UniSchedule")

    st.markdown("#### Fiches Enrôlements")
    st.caption(
        "Téléchargez votre fiche d'enrôlement officielle ou votre rapport de présences "
        "pour chaque session."
    )
    st.divider()

    _SESSIONS = [
        "S1 - Session Normale",
        "S1 - Session de Rattrapage",
        "S2 - Session Normale",
        "S2 - Session de Rattrapage",
    ]

    if not _prog_fiche:
        st.info("📭 Aucun cours enregistré pour votre classe. "
                "Les fiches seront disponibles une fois le programme chargé.")
    else:
        for _sess in _SESSIONS:
            with st.expander(f"📄 FICHE D'EXAMEN — {_sess.upper()}"):
                _col_fiche, _col_att = st.columns(2)

                # Fiche d'enrôlement
                with _col_fiche:
                    try:
                        _pdf_enroll = generate_enrollment_pdf(
                            student_name   = _display_name,
                            student_number = student["student_number"],
                            university_name= _uni_name,
                            faculty_name   = _fac_name,
                            department_name= _dept_name,
                            promotion_name = _promo_name,
                            filiere_name   = _cls_fiche.get("filiere_name","") if _cls_fiche else "",
                            option_name    = _cls_fiche.get("option_name","")  if _cls_fiche else "",
                            academic_year  = _ay_label_fiche,
                            session_name   = _sess,
                            programme      = _prog_fiche,
                            class_name     = _cls_fiche["name"] if _cls_fiche else "",
                        )
                        st.download_button(
                            "⬇️ Télécharger la fiche",
                            data=_pdf_enroll,
                            file_name=(
                                f"fiche_enrolement_{student['student_number']}_"
                                f"{_sess.replace(' ', '_').replace('-','')}.pdf"
                            ),
                            mime="application/pdf",
                            key=f"dl_enroll_{_sess}",
                            use_container_width=True,
                            type="primary",
                        )
                    except Exception as _epdf:
                        st.error(f"Erreur génération fiche : {_epdf}")

                # Rapport de présences
                with _col_att:
                    try:
                        _pdf_att = generate_attendance_report_pdf(
                            student_name   = _display_name,
                            student_number = student["student_number"],
                            university_name= _uni_name,
                            class_name     = _cls_fiche["name"] if _cls_fiche else "",
                            academic_year  = _ay_label_fiche,
                            attendance_stats = _att_fiche,
                        )
                        st.download_button(
                            "⬇️ Télécharger rapport des présences",
                            data=_pdf_att,
                            file_name=(
                                f"rapport_presences_{student['student_number']}_"
                                f"{_sess.replace(' ', '_').replace('-','')}.pdf"
                            ),
                            mime="application/pdf",
                            key=f"dl_att_{_sess}",
                            use_container_width=True,
                        )
                    except Exception as _epdf2:
                        st.error(f"Erreur génération rapport : {_epdf2}")


with tab_compte:
    from db.queries import StudentRegistryQueries as _SRQ_cpt
    from utils.storage import upload_file, get_file_bytes as _get_img_bytes

    # Charger la fiche registre de l'étudiant
    try:
        _reg = _SRQ_cpt.get_by_student_id(student["id"]) or {}
    except Exception:
        _reg = {}

    _sub_profil, _sub_pwd = st.tabs(["👤 Mon Profil", "🔑 Mot de passe"])

    # ── Sous-onglet : Profil enrichi ──────────────────────────────────────────
    with _sub_profil:
        st.markdown(f"**Numéro étudiant :** {student['student_number']}  ·  **@{_username}**")
        st.divider()

        # ── Photo passeport ───────────────────────────────────────────────────
        _photo_url = _reg.get("photo_passeport_url") or ""
        _col_photo, _col_info = st.columns([1, 3])
        with _col_photo:
            if _photo_url:
                try:
                    _img_bytes = _get_img_bytes(_photo_url)
                    if _img_bytes:
                        st.image(_img_bytes, width=130, caption="Photo passeport")
                    else:
                        st.caption("Photo indisponible")
                except Exception:
                    st.caption("Photo indisponible")
            else:
                st.markdown(
                    "<div style='width:130px;height:160px;background:#E2E8F0;"
                    "border-radius:8px;display:flex;align-items:center;"
                    "justify-content:center;color:#94A3B8;font-size:2rem'>👤</div>",
                    unsafe_allow_html=True
                )
            _new_photo = st.file_uploader(
                "Changer la photo", type=["jpg","jpeg","png"],
                key="upload_photo_passeport", label_visibility="collapsed"
            )
            if _new_photo:
                if st.button("📤 Enregistrer la photo", key="btn_save_photo",
                             use_container_width=True):
                    try:
                        _photo_bytes = _new_photo.read()
                        _stored, _ = upload_file(
                            _photo_bytes, _new_photo.name,
                            "student-photos", folder=str(student["id"])
                        )
                        _SRQ_cpt.update_profile(_reg["id"], photo_passeport_url=_stored)
                        st.success("Photo enregistrée !")
                        st.rerun()
                    except Exception as _ep:
                        st.error(f"Erreur upload : {_ep}")
        with _col_info:
            st.caption("Photo passeport — utilisable pour les documents officiels (visage uniquement svp)")

        st.divider()

        # ── Formulaire profil ─────────────────────────────────────────────────
        with st.form("profil_form"):
            # Section 1 : Informations personnelles
            st.markdown("##### Informations personnelles")
            _pc1, _pc2, _pc3 = st.columns(3)
            _f_nom     = _pc1.text_input("Nom *",     value=_reg.get("nom") or "")
            _f_postnom = _pc2.text_input("Postnom",   value=_reg.get("postnom") or "")
            _f_prenom  = _pc3.text_input("Prénom",    value=_reg.get("prenom") or "")

            _pc4, _pc5 = st.columns(2)
            _f_email = _pc4.text_input("Email",
                value=student.get("email") or "", disabled=True)
            _f_tel   = _pc5.text_input("Téléphone",
                value=_reg.get("telephone") or "",
                placeholder="+243 ...")

            _pc6, _pc7, _pc8 = st.columns(3)
            _f_sexe = _pc6.selectbox("Sexe",
                ["", "Masculin", "Féminin"],
                index=["", "Masculin", "Féminin"].index(_reg.get("sexe") or "")
                if _reg.get("sexe") in ["", "Masculin", "Féminin"] else 0)
            _f_ddn = _pc7.date_input("Date de naissance",
                value=_reg.get("date_naissance") or None,
                format="DD/MM/YYYY", min_value=None)
            _f_lieu_nais = _pc8.text_input("Lieu de naissance",
                value=_reg.get("lieu_naissance") or "")

            _pc9, _pc10 = st.columns(2)
            _f_nationalite = _pc9.text_input("Nationalité",
                value=_reg.get("nationalite") or "", placeholder="Ex : Congolaise(RDC)")
            _f_etat_civil  = _pc10.selectbox("État civil",
                ["", "Célibataire", "Marié(e)", "Divorcé(e)", "Veuf/Veuve"],
                index=["", "Célibataire", "Marié(e)", "Divorcé(e)", "Veuf/Veuve"].index(
                    _reg.get("etat_civil") or "")
                if (_reg.get("etat_civil") or "") in
                    ["", "Célibataire", "Marié(e)", "Divorcé(e)", "Veuf/Veuve"] else 0)

            st.divider()

            # Section 2 : Adresse
            st.markdown("##### Adresse")
            _pa1, _pa2 = st.columns(2)
            _f_province  = _pa1.text_input("Province d'origine",
                value=_reg.get("province") or "")
            _f_district  = _pa2.text_input("District",
                value=_reg.get("district") or "")

            _pa3, _pa4 = st.columns(2)
            _f_territoire = _pa3.text_input("Territoire",
                value=_reg.get("territoire") or "")
            _f_secteur    = _pa4.text_input("Secteur",
                value=_reg.get("secteur") or "")

            _pa5, _pa6 = st.columns(2)
            _f_commune  = _pa5.text_input("Commune",
                value=_reg.get("commune") or "")
            _f_adresse  = _pa6.text_input("Adresse domicile",
                value=_reg.get("adresse_domicile") or "")

            st.divider()

            # Section 3 : Contact d'urgence
            st.markdown("##### Contact d'urgence")
            _pu1, _pu2, _pu3 = st.columns(3)
            _f_urg_nom = _pu1.text_input("Nom de la personne *",
                value=_reg.get("contact_urgence_nom") or "")
            _f_urg_tel = _pu2.text_input("Téléphone *",
                value=_reg.get("contact_urgence_tel") or "")
            _f_urg_adr = _pu3.text_input("Adresse",
                value=_reg.get("contact_urgence_adresse") or "")

            st.divider()

            # Section 4 : Diplôme
            st.markdown("##### Diplôme d'accès")
            _pd1, _pd2 = st.columns(2)
            _f_dip_type  = _pd1.selectbox("Type de diplôme",
                ["", "BAC", "A2", "Licence", "Master", "Autre"],
                index=["", "BAC", "A2", "Licence", "Master", "Autre"].index(
                    _reg.get("diplome_type") or "")
                if (_reg.get("diplome_type") or "") in
                    ["", "BAC", "A2", "Licence", "Master", "Autre"] else 0)
            _f_dip_num   = _pd2.text_input("Numéro du diplôme",
                value=_reg.get("diplome_numero") or "")

            _pd3, _pd4 = st.columns(2)
            _f_dip_sect = _pd3.text_input("Section du diplôme",
                value=_reg.get("diplome_section") or "",
                placeholder="Ex : Sciences, Lettres...")
            _f_dip_etab = _pd4.text_input("Établissement",
                value=_reg.get("diplome_etablissement") or "")

            _f_dip_annee = st.text_input("Année d'obtention",
                value=_reg.get("diplome_annee") or "",
                placeholder="Ex : 2023-2024")

            st.divider()

            _sb1, _sb2, _ = st.columns([1, 1, 3])
            _submitted = _sb1.form_submit_button("✅ Modifier", type="primary",
                                                  use_container_width=True)
            _cancelled = _sb2.form_submit_button("✖️ Annuler",
                                                  use_container_width=True)

            if _submitted and _reg.get("id"):
                try:
                    _SRQ_cpt.update_profile(
                        registry_id=_reg["id"],
                        telephone=_f_tel,
                        lieu_naissance=_f_lieu_nais,
                        nationalite=_f_nationalite,
                        etat_civil=_f_etat_civil,
                        province=_f_province,
                        district=_f_district,
                        territoire=_f_territoire,
                        secteur=_f_secteur,
                        commune=_f_commune,
                        adresse_domicile=_f_adresse,
                        contact_urgence_nom=_f_urg_nom,
                        contact_urgence_tel=_f_urg_tel,
                        contact_urgence_adresse=_f_urg_adr,
                        diplome_type=_f_dip_type,
                        diplome_numero=_f_dip_num,
                        diplome_section=_f_dip_sect,
                        diplome_etablissement=_f_dip_etab,
                        diplome_annee=_f_dip_annee,
                    )
                    st.success("✅ Profil mis à jour avec succès !")
                    st.rerun()
                except Exception as _ef:
                    st.error(f"Erreur : {_ef}")
            elif _submitted and not _reg.get("id"):
                st.warning("Votre fiche registre est introuvable. Contactez l'administration.")

    # ── Sous-onglet : Mot de passe ────────────────────────────────────────────
    with _sub_pwd:
        st.markdown("##### 🔑 Changer mon mot de passe")
        with st.form("change_pwd_form"):
            cur_pwd  = st.text_input("Mot de passe actuel *", type="password",
                                     placeholder="••••••••")
            col_np1, col_np2 = st.columns(2)
            with col_np1:
                new_pwd1 = st.text_input("Nouveau mot de passe *", type="password",
                                         placeholder="Min 8 caractères")
            with col_np2:
                new_pwd2 = st.text_input("Confirmer *", type="password",
                                         placeholder="••••••••")
            if st.form_submit_button("✅ Enregistrer le nouveau mot de passe",
                                     type="primary"):
                ok, msg = change_student_password(
                    student_id=student["id"],
                    current_password=cur_pwd,
                    new_password=new_pwd1,
                    confirm=new_pwd2,
                )
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
        st.caption("Si vous avez oublié votre mot de passe, contactez l'administration.")
