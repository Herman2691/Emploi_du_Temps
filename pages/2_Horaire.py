# pages/2_Horaire.py
import streamlit as st
from io import BytesIO
from datetime import datetime, timedelta, time as dt_time
from db.queries import (FacultyQueries, DepartmentQueries, PromotionQueries,
                        ClassQueries, ScheduleQueries, CourseQueries,
                        ProfessorQueries, AnnouncementQueries, UniversityQueries)
from utils.components import inject_global_css, announcement_card, week_nav, get_logo_display_url
from utils.pdf_export import generate_schedule_pdf

inject_global_css()


def _darken(hex_color: str, factor: float = 0.65) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02X}{:02X}{:02X}".format(int(r*factor), int(g*factor), int(b*factor))


def _inject_uni_color(color: str):
    if not color or color.upper() == "#2563EB":
        return
    dark = _darken(color)
    st.markdown(f"""
    <style>
        .class-banner {{
            background: linear-gradient(90deg, {dark}, {color}) !important;
        }}
        table.sched th   {{ background: {color} !important; border-color: {dark} !important; }}
        table.sched th.time-th {{ background: {dark} !important; }}
        .slot {{ border-left-color: {color} !important; }}
    </style>
    """, unsafe_allow_html=True)


def _generate_qr(url: str) -> bytes:
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1, box_size=8, border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E293B", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return None


def _get_share_url(cls_id: int) -> str:
    try:
        base = st.secrets.get("app_url", "http://localhost:8501").rstrip("/")
    except Exception:
        base = "http://localhost:8501"
    return f"{base}/Horaire?cls={cls_id}"

st.markdown("""
<style>
    .selectors-bar {
        background: white;
        border: 1px solid #E8EFF8;
        border-top: 3px solid #2563EB;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(37,99,235,0.07), 0 1px 3px rgba(0,0,0,0.04);
    }
    .class-banner {
        background: linear-gradient(135deg, #1E293B 0%, #1E40AF 60%, #2563EB 100%);
        color: white; border-radius: 14px;
        padding: 1rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 18px rgba(37,99,235,0.30);
        position: relative; overflow: hidden;
    }
    .class-banner::after {
        content: "";
        position: absolute; top: -30px; right: -30px;
        width: 120px; height: 120px; border-radius: 50%;
        background: rgba(255,255,255,0.06);
    }
    .class-banner h3 { margin:0; font-family:'Poppins',sans-serif; font-size:1.1rem; font-weight:700; }
    .class-banner span { font-size:0.82rem; opacity:0.82; }
</style>
""", unsafe_allow_html=True)


# ── FIX 1 : Convertit proprement TIME/timedelta → "HH:MM" ────────────────────
def fmt_time(t) -> str:
    """Convertit datetime.time ou datetime.timedelta en string HH:MM."""
    if t is None:
        return "--:--"
    if isinstance(t, timedelta):
        total = int(t.total_seconds())
        h, m  = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    if isinstance(t, dt_time):
        return t.strftime("%H:%M")
    # Fallback string
    return str(t)[:5].zfill(5)


# ── Lien direct : ?cls=X — charge la classe sans passer par les sélecteurs ───
_direct_cls_id = st.query_params.get("cls")
_direct_mode   = False
_direct_cls    = None

if _direct_cls_id:
    try:
        _full = ClassQueries.get_by_id_full(int(_direct_cls_id))
        if _full:
            _direct_mode = True
            _direct_cls  = _full
            # Nettoyer le param pour éviter qu'il persiste après navigation
            st.query_params.clear()
    except Exception:
        pass

# ── Mode étudiant connecté : auto-charge son emploi du temps ─────────────────
if not _direct_mode:
    _stu_sess = st.session_state.get("student")
    if _stu_sess and _stu_sess.get("class_id"):
        try:
            _stu_full = ClassQueries.get_by_id_full(int(_stu_sess["class_id"]))
            if _stu_full:
                _direct_mode = True
                _direct_cls  = _stu_full
        except Exception:
            pass

# ── Navigation directe (sidebar) sans université pré-sélectionnée ─────────────
uni_id   = st.session_state.get("sel_uni_id")
uni_name = st.session_state.get("sel_uni_name", "")

if _direct_mode and _direct_cls:
    # ── Mode lien direct : afficher l'horaire sans sélecteurs ────────────────
    d = _direct_cls
    st.markdown(
        f"<div style='font-size:0.85rem;color:#64748B;margin-bottom:1rem'>"
        f"🏠 {d['university_name']} › {d['faculty_name']} › "
        f"{d['department_name']} › {d['promotion_name']} › {d['name']}"
        f"</div>",
        unsafe_allow_html=True,
    )
    try:
        schedules_d     = ScheduleQueries.get_by_class(d["id"])
        courses_d       = CourseQueries.get_by_class(d["id"])
        professors_d    = ProfessorQueries.get_by_department(d["department_id"])
        announcements_d = AnnouncementQueries.get_by_class(d["id"])
        _uni_d          = UniversityQueries.get_by_id(d["university_id"])
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}"); st.stop()

    _uni_logo_url_d = get_logo_display_url((_uni_d or {}).get("photo_url",""))
    _banner_html_d = f"""
    <div class="class-banner">
        <h3 style="margin:0">🏫 Classe {d['name']} &nbsp;·&nbsp; {d['promotion_name']}</h3>
        <span style="font-size:0.82rem;opacity:0.85">{d['department_name']} · {d['faculty_name']}</span>
    </div>
    """
    if _uni_logo_url_d:
        _bc1_d, _bc2_d = st.columns([0.6, 6])
        with _bc1_d:
            st.image(_uni_logo_url_d, width=44)
        with _bc2_d:
            st.markdown(_banner_html_d, unsafe_allow_html=True)
    else:
        st.markdown(_banner_html_d, unsafe_allow_html=True)

    _inject_uni_color((_uni_d or {}).get("primary_color", "#2563EB"))

    tab_h_d, tab_c_d, tab_p_d, tab_a_d = st.tabs([
        "📅 Emploi du Temps",
        f"📘 Cours ({len(courses_d)})",
        f"👨‍🏫 Professeurs ({len(professors_d)})",
        f"📢 Communiqués ({len(announcements_d)})",
    ])
    with tab_h_d:
        _dd_d, _wt_d, _wn_d, _mon_d = week_nav("wf_d")
        _sat_d = _mon_d + timedelta(days=6)
        filtered_d = []
        for _s in schedules_d:
            if _s.get("week_type") not in ("Toutes", _wt_d):
                continue
            _vf = _s.get("valid_from")
            _vu = _s.get("valid_until")
            if _vf is not None and _sat_d < _vf:
                continue
            if _vu is not None and _mon_d > _vu:
                continue
            filtered_d.append(_s)
        if not filtered_d:
            st.info("📭 Aucun cours planifié pour cette semaine.")
        else:
            from utils.components import render_schedule_table
            render_schedule_table(filtered_d, day_dates=_dd_d)
    with tab_c_d:
        for c in courses_d:
            code_s = f"[{c['code']}]" if c.get("code") else ""
            st.markdown(
                f"<div style='padding:0.6rem 1rem;background:white;"
                f"border:1px solid #E2E8F0;border-radius:10px;margin-bottom:0.5rem;"
                f"display:flex;justify-content:space-between'>"
                f"<span style='font-weight:600'>{code_s} {c['name']}</span>"
                f"<span style='color:#64748B;font-size:0.82rem'>"
                f"⏱ {c.get('hours',0)}h · Coeff. {c.get('weight',1.0)}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    with tab_p_d:
        cols_p = st.columns(2)
        for i, p in enumerate(professors_d):
            with cols_p[i % 2]:
                st.markdown(
                    f"<div style='background:white;border:1px solid #E2E8F0;"
                    f"border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.5rem'>"
                    f"<b>{p['name']}</b><br>"
                    f"<span style='color:#94A3B8;font-size:0.78rem'>"
                    f"{'✉️ '+p['email'] if p.get('email') else ''}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    with tab_a_d:
        if not announcements_d:
            st.info("Aucun communiqué.")
        else:
            for ann in announcements_d:
                announcement_card(ann)

    # ── Export PDF (mode direct) ──────────────────────────────────────────────
    with st.expander("📄 Exporter en PDF"):
        _d_week = st.selectbox("Semaines", ["Toutes","Paire","Impaire"],
                               key="d_pdf_week")
        try:
            _d_pdf = generate_schedule_pdf(
                class_name=d["name"],
                promotion_name=d["promotion_name"],
                department_name=d["department_name"],
                faculty_name=d["faculty_name"],
                university_name=d["university_name"],
                schedules=schedules_d,
                week_filter=_d_week,
            )
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=_d_pdf,
                file_name=f"EDT_{d['name'].replace(' ','_')}_{_d_week}.pdf",
                mime="application/pdf",
                type="primary",
            )
        except Exception as _e:
            st.error(f"Erreur : {_e}")
        st.caption("Format A4 paysage — imprimable en une page.")

    # ── Partager (mode direct) ────────────────────────────────────────────────
    _share_url_d = _get_share_url(d["id"])
    with st.expander("🔗 Partager / QR Code"):
        st.text_input("Lien direct", value=_share_url_d,
                      disabled=True, label_visibility="collapsed")
        st.caption("Copiez ce lien ou scannez le QR code — s'ouvre directement sur cet horaire")
        qr_bytes = _generate_qr(_share_url_d)
        if qr_bytes:
            _, col_qr, _ = st.columns([1, 1, 1])
            with col_qr:
                st.image(qr_bytes, width=220)
                st.download_button(
                    "⬇️ Télécharger le QR Code",
                    data=qr_bytes,
                    file_name=f"qr_{d['name'].replace(' ','_')}.png",
                    mime="image/png",
                    use_container_width=True,
                )
    st.stop()

# ── Mode professeur connecté : affiche tous ses cours ────────────────────────
if not _direct_mode:
    _user_sess = st.session_state.get("user")
    _is_prof_mode = (
        _user_sess and (
            str(_user_sess.get("role", "")).strip().lower() == "professeur"
            or _user_sess.get("professor_id") is not None
        )
    )
    if _is_prof_mode:
        _prof_id   = _user_sess.get("professor_id") or _user_sess.get("id")
        _prof_name = _user_sess.get("name", "Professeur")
        st.markdown(f"""
        <div class="class-banner">
            <h3 style="margin:0">👨‍🏫 {_prof_name}</h3>
            <span style="font-size:0.82rem;opacity:0.85">Tous mes cours — toutes classes confondues</span>
        </div>
        """, unsafe_allow_html=True)
        try:
            _all_sched_p = ScheduleQueries.get_by_professor(_prof_id)
        except Exception as _pe:
            st.error(f"❌ Erreur chargement horaires : {_pe}")
            st.stop()
        if not _all_sched_p:
            st.info("📭 Aucun cours planifié pour le moment.")
            st.stop()
        _dd_p, _wt_p, _wn_p, _mon_p = week_nav("wf_prof")
        _sat_p = _mon_p + timedelta(days=6)
        _filtered_p = [
            s for s in _all_sched_p
            if s.get("week_type") in ("Toutes", _wt_p)
            and (s.get("valid_from") is None or _sat_p >= s["valid_from"])
            and (s.get("valid_until") is None or _mon_p <= s["valid_until"])
        ]
        DAYS_P = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
        _list_view_p = st.toggle("📱 Vue liste (mobile)", key="list_view_prof")
        if not _filtered_p:
            st.info("📭 Aucun cours planifié pour cette semaine.")
        elif _list_view_p:
            for _dayp in DAYS_P:
                _day_slots_p = [s for s in _filtered_p if s["day"] == _dayp]
                if not _day_slots_p:
                    continue
                st.markdown(f"**{_dayp}** · {_dd_p.get(_dayp, '')}")
                for s in sorted(_day_slots_p, key=lambda x: x["start_time"]):
                    _rm_p = s.get("room_name") or s.get("room") or ""
                    _rm_str_p = f" · 📍 {_rm_p}" if _rm_p else ""
                    st.markdown(f"""
                    <div style="background:#EFF6FF;border-left:4px solid #2563EB;
                                border-radius:8px;padding:0.6rem 1rem;margin-bottom:0.5rem">
                      <div style="font-weight:700;font-size:0.9rem">{s['course_name']}</div>
                      <div style="color:#64748B;font-size:0.8rem">
                        {fmt_time(s['start_time'])}–{fmt_time(s['end_time'])} ·
                        🏫 {s.get('class_name','')} ({s.get('department_name','')}){_rm_str_p}
                      </div>
                    </div>""", unsafe_allow_html=True)
                st.divider()
        else:
            _time_slots_p = sorted(set(
                (fmt_time(s["start_time"]), fmt_time(s["end_time"]))
                for s in _filtered_p
            ))
            _grid_p = {slot: {day: [] for day in DAYS_P} for slot in _time_slots_p}
            for s in _filtered_p:
                _slotp = (fmt_time(s["start_time"]), fmt_time(s["end_time"]))
                _dayp  = s["day"]
                if _dayp in DAYS_P and _slotp in _grid_p:
                    _grid_p[_slotp][_dayp].append(s)
            _html_p  = '<div class="sched-wrap"><table class="sched"><thead><tr>'
            _html_p += '<th class="time-th">⏱ Heure</th>'
            for _dayp in DAYS_P:
                _dlbl_p = f"<span class='day-date'>{_dd_p[_dayp]}</span>"
                _html_p += f'<th>{_dayp}{_dlbl_p}</th>'
            _html_p += '</tr></thead><tbody>'
            for (_start_p, _end_p) in _time_slots_p:
                _html_p += (
                    f'<tr><td class="time-td">'
                    f'<span style="color:#1E293B;font-size:0.80rem">{_start_p}</span>'
                    f'<br><span style="color:#CBD5E1;font-size:0.58rem">▼</span>'
                    f'<br><span style="color:#1E293B;font-size:0.80rem">{_end_p}</span>'
                    f'</td>'
                )
                for _dayp in DAYS_P:
                    _html_p += '<td>'
                    for s in _grid_p[(_start_p, _end_p)][_dayp]:
                        _rm_p     = s.get("room_name") or s.get("room") or "—"
                        _status_p = s.get("slot_status") or "actif"
                        _opac_p   = "0.42" if _status_p == "annule" else "1"
                        _html_p += (
                            f'<div class="slot slot-cours" style="opacity:{_opac_p}">'
                            f'<div class="sn sn-cours">{s["course_name"]}</div>'
                            f'<div class="sp sp-cours">🏫 {s.get("class_name","")}</div>'
                            f'<div class="sr sr-cours">📍 {_rm_p}</div>'
                            f'</div>'
                        )
                    _html_p += '</td>'
                _html_p += '</tr>'
            _html_p += '</tbody></table></div>'
            st.markdown(_html_p, unsafe_allow_html=True)
        st.stop()

if not uni_id:
    # L'étudiant arrive directement par la sidebar → lui laisser choisir l'université ici
    st.markdown("### 🏛️ Choisissez d'abord votre université")
    try:
        all_unis = UniversityQueries.get_all()
    except Exception as e:
        st.error(f"❌ Erreur connexion : {e}"); st.stop()

    if not all_unis:
        st.info("Aucune université disponible."); st.stop()

    uni_choice = st.selectbox("Université", options=all_unis,
                               format_func=lambda u: u["name"],
                               index=None, placeholder="— Sélectionner —")
    if uni_choice:
        st.session_state["sel_uni_id"]   = uni_choice["id"]
        st.session_state["sel_uni_name"] = uni_choice["name"]
        st.rerun()
    st.stop()

# ── Barre retour ──────────────────────────────────────────────────────────────
col_back, col_title = st.columns([1, 6])
with col_back:
    if st.button("← Accueil"):
        # FIX 3 : Nettoie tous les sélecteurs au retour
        for k in ["sel_uni_id","sel_uni_name","sel_fac","sel_dept","sel_promo","sel_cls"]:
            st.session_state.pop(k, None)
        st.switch_page("pages/1_Accueil.py")
with col_title:
    st.markdown(f"<h3 style='margin:0;color:#1E293B;font-family:Poppins,sans-serif'>🏛️ {uni_name}</h3>",
                unsafe_allow_html=True)

st.markdown("<hr style='border:none;border-top:1px solid #E2E8F0;margin:0.75rem 0 1.25rem'>",
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SÉLECTEURS EN CASCADE avec reset automatique
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="selectors-bar">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4, gap="medium")

# ── Faculté ──────────────────────────────────────────────────────────────────
with c1:
    try:
        faculties = FacultyQueries.get_by_university(uni_id)
    except Exception as e:
        st.error(f"Erreur : {e}"); faculties = []

    fac_options  = {f["name"]: f for f in faculties}
    fac_sel_name = st.selectbox("📚 Faculté",
                                ["— Choisir —"] + list(fac_options.keys()),
                                key="sel_fac")
    fac = fac_options.get(fac_sel_name)

    # FIX 4 : Reset cascade si faculté change
    if "prev_fac" not in st.session_state:
        st.session_state["prev_fac"] = fac_sel_name
    if st.session_state["prev_fac"] != fac_sel_name:
        for k in ["sel_dept","sel_promo","sel_cls"]:
            st.session_state.pop(k, None)
        st.session_state["prev_fac"] = fac_sel_name
        st.rerun()

# ── Département ──────────────────────────────────────────────────────────────
with c2:
    dept, dept_options = None, {}
    if fac:
        try:
            departments = DepartmentQueries.get_by_faculty(fac["id"])
        except Exception as e:
            st.error(f"Erreur : {e}"); departments = []
        dept_options = {d["name"]: d for d in departments}

    dept_sel_name = st.selectbox("🏢 Département",
                                 ["— Choisir —"] + list(dept_options.keys()),
                                 key="sel_dept", disabled=not fac)
    dept = dept_options.get(dept_sel_name)

    if "prev_dept" not in st.session_state:
        st.session_state["prev_dept"] = dept_sel_name
    if st.session_state["prev_dept"] != dept_sel_name:
        for k in ["sel_promo","sel_cls"]:
            st.session_state.pop(k, None)
        st.session_state["prev_dept"] = dept_sel_name
        st.rerun()

# ── Promotion ────────────────────────────────────────────────────────────────
with c3:
    promo, promo_options = None, {}
    if dept:
        try:
            promotions = PromotionQueries.get_by_department(dept["id"])
        except Exception as e:
            st.error(f"Erreur : {e}"); promotions = []
        promo_options = {f"{p['name']} ({p['academic_year']})": p for p in promotions}

    promo_sel_name = st.selectbox("🎓 Promotion",
                                  ["— Choisir —"] + list(promo_options.keys()),
                                  key="sel_promo", disabled=not dept)
    promo = promo_options.get(promo_sel_name)

    if "prev_promo" not in st.session_state:
        st.session_state["prev_promo"] = promo_sel_name
    if st.session_state["prev_promo"] != promo_sel_name:
        st.session_state.pop("sel_cls", None)
        st.session_state["prev_promo"] = promo_sel_name
        st.rerun()

# ── Classe ────────────────────────────────────────────────────────────────────
with c4:
    cls, cls_options = None, {}
    if promo:
        try:
            classes = ClassQueries.get_by_promotion(promo["id"])
        except Exception as e:
            st.error(f"Erreur : {e}"); classes = []
        cls_options = {c["name"]: c for c in classes}

    cls_sel_name = st.selectbox("🏫 Classe",
                                ["— Choisir —"] + list(cls_options.keys()),
                                key="sel_cls", disabled=not promo)
    cls = cls_options.get(cls_sel_name)

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONTENU — affiché seulement quand une classe est choisie
# ══════════════════════════════════════════════════════════════════════════════
if not cls:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0">
        <div style="font-size:4rem">📅</div>
        <p style="font-size:1.05rem;margin-top:0.5rem;color:#94A3B8">
            Sélectionnez votre faculté, département, promotion et classe<br>
            pour afficher votre emploi du temps
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Chargement des données
try:
    schedules     = ScheduleQueries.get_by_class(cls["id"])
    courses       = CourseQueries.get_by_class(cls["id"])
    professors    = ProfessorQueries.get_by_department(dept["id"])
    announcements = AnnouncementQueries.get_by_class(cls["id"])
    _uni_data     = UniversityQueries.get_by_id(uni_id)
except Exception as e:
    st.error(f"❌ Erreur chargement données : {e}"); st.stop()

# Appliquer la couleur de l'université
_uni_color = (_uni_data or {}).get("primary_color", "#2563EB")
_inject_uni_color(_uni_color)

# ── Bannière classe ───────────────────────────────────────────────────────────
promo_label = promo_sel_name.split(" (")[0]
col_banner, col_pdf, col_share = st.columns([5, 1, 1])
with col_banner:
    _uni_logo_url = get_logo_display_url((_uni_data or {}).get("photo_url",""))
    if _uni_logo_url:
        _bc1, _bc2 = st.columns([0.6, 6])
        with _bc1:
            st.image(_uni_logo_url, width=44)
        with _bc2:
            st.markdown(f"""
    <div class="class-banner">
        <h3 style="margin:0">🏫 Classe {cls['name']} &nbsp;·&nbsp; {promo_label}</h3>
        <span style="font-size:0.82rem;opacity:0.85">{dept['name']} · {fac['name']}</span>
    </div>
    """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
    <div class="class-banner">
        <h3 style="margin:0">🏫 Classe {cls['name']} &nbsp;·&nbsp; {promo_label}</h3>
        <span style="font-size:0.82rem;opacity:0.85">{dept['name']} · {fac['name']}</span>
    </div>
    """, unsafe_allow_html=True)
with col_pdf:
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    if st.button("📄 PDF", use_container_width=True, key="btn_pdf"):
        st.session_state["show_pdf"] = not st.session_state.get("show_pdf", False)
with col_share:
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    if st.button("🔗 Partager", use_container_width=True, key="btn_share"):
        st.session_state["show_share"] = not st.session_state.get("show_share", False)

# ── Export PDF ────────────────────────────────────────────────────────────────
if st.session_state.get("show_pdf"):
    with st.container():
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                    padding:1.25rem 1.5rem;margin-bottom:1rem">
        """, unsafe_allow_html=True)
        st.markdown("##### 📄 Exporter l'emploi du temps en PDF")
        _pdf_col1, _pdf_col2, _pdf_col3 = st.columns([2, 2, 3])
        with _pdf_col1:
            _pdf_week = st.selectbox(
                "Semaines à inclure",
                ["Toutes", "Paire", "Impaire"],
                key="pdf_week_filter",
            )
        with _pdf_col2:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            try:
                _pdf_bytes = generate_schedule_pdf(
                    class_name=cls["name"],
                    promotion_name=promo_label,
                    department_name=dept["name"],
                    faculty_name=fac["name"],
                    university_name=uni_name,
                    schedules=schedules,
                    week_filter=_pdf_week,
                )
                _fname = f"EDT_{cls['name'].replace(' ','_')}_{_pdf_week}.pdf"
                st.download_button(
                    label="⬇️ Télécharger le PDF",
                    data=_pdf_bytes,
                    file_name=_fname,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as _e:
                st.error(f"Erreur génération PDF : {_e}")
        with _pdf_col3:
            st.caption(
                "Le PDF est en format A4 paysage. "
                "Imprimez-le en une seule page pour l'afficher en classe."
            )
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("show_share"):
    _share_url = _get_share_url(cls["id"])
    with st.container():
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                    padding:1.25rem 1.5rem;margin-bottom:1rem">
        """, unsafe_allow_html=True)
        st.markdown("##### 🔗 Lien direct vers cet emploi du temps")
        st.text_input("URL à partager", value=_share_url,
                      disabled=True, label_visibility="collapsed")
        st.caption(
            "Ce lien s'ouvre directement sur l'horaire de cette classe — "
            "sans passer par les menus."
        )
        qr_bytes = _generate_qr(_share_url)
        if qr_bytes:
            col_qr_a, col_qr_b, col_qr_c = st.columns([1, 1, 1])
            with col_qr_b:
                st.image(qr_bytes, width=220,
                         caption=f"QR Code — Classe {cls['name']}")
                st.download_button(
                    "⬇️ Télécharger le QR Code",
                    data=qr_bytes,
                    file_name=f"qr_{cls['name'].replace(' ','_')}.png",
                    mime="image/png",
                    use_container_width=True,
                )
        else:
            st.warning("Installez `qrcode[pil]` pour générer le QR code.")
        st.markdown("</div>", unsafe_allow_html=True)

# ── Onglets ───────────────────────────────────────────────────────────────────
tab_h, tab_c, tab_p, tab_a = st.tabs([
    "📅 Emploi du Temps",
    f"📘 Cours ({len(courses)})",
    f"👨‍🏫 Professeurs ({len(professors)})",
    f"📢 Communiqués ({len(announcements)})",
])

# ── ONGLET 1 : GRILLE HORAIRE ─────────────────────────────────────────────────
with tab_h:
    _day_dates, _week_type, _week_num, _monday = week_nav("wf")
    _saturday = _monday + timedelta(days=6)
    filtered = []
    for _s in schedules:
        if _s.get("week_type") not in ("Toutes", _week_type):
            continue
        _vf = _s.get("valid_from")
        _vu = _s.get("valid_until")
        if _vf is not None and _saturday < _vf:
            continue
        if _vu is not None and _monday > _vu:
            continue
        filtered.append(_s)

    if not filtered:
        st.info("📭 Aucun cours planifié pour cette semaine.")
    else:
        DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

        # ── Mobile list view toggle ───────────────────────────────────────────
        _list_view = st.toggle("📱 Vue liste (mobile)", key="list_view_toggle")
        if _list_view:
            for day in DAYS:
                day_slots = [s for s in filtered if s["day"] == day]
                if not day_slots:
                    continue
                date_lbl = _day_dates.get(day, "")
                st.markdown(f"**{day}** · {date_lbl}")
                for s in sorted(day_slots, key=lambda x: x["start_time"]):
                    _st2   = s.get("slot_type", "cours")
                    _color  = {"cours": "#EFF6FF", "examen": "#F0FDF4", "ferie": "#FEF2F2"}.get(_st2, "#EFF6FF")
                    _border = {"cours": "#2563EB", "examen": "#16A34A", "ferie": "#DC2626"}.get(_st2, "#2563EB")
                    _status  = s.get("slot_status", "actif")
                    _opacity = "0.5" if _status == "annule" else "1"
                    _label   = "ANNULE — " if _status == "annule" else ("REMPLACE " if _status == "remplace" else "")
                    _sub     = s.get("substitute_name")
                    _prof_disp = f"Rempl: {_sub}" if _sub else s.get("professor_name", "")
                    _room_str = f" · Salle: {s['room']}" if s.get("room") else ""
                    _prof_str = f" · Prof: {_prof_disp}" if _prof_disp else ""
                    st.markdown(f"""
                    <div style="background:{_color};border-left:4px solid {_border};
                                border-radius:8px;padding:0.6rem 1rem;margin-bottom:0.5rem;
                                opacity:{_opacity}">
                      <div style="font-weight:700;font-size:0.9rem">{_label}{s['course_name']}</div>
                      <div style="color:#64748B;font-size:0.8rem">
                        {fmt_time(s['start_time'])}–{fmt_time(s['end_time'])}{_prof_str}{_room_str}
                      </div>
                    </div>""", unsafe_allow_html=True)
                st.divider()
        else:
            time_slots = sorted(set(
                (fmt_time(s["start_time"]), fmt_time(s["end_time"]))
                for s in filtered
            ))

            grid = {slot: {day: [] for day in DAYS} for slot in time_slots}
            for s in filtered:
                slot = (fmt_time(s["start_time"]), fmt_time(s["end_time"]))
                day  = s["day"]
                if day in DAYS and slot in grid:
                    grid[slot][day].append(s)

            from utils.components import _initials as _av_init
            html  = '<div class="sched-wrap"><table class="sched"><thead><tr>'
            html += '<th class="time-th">⏱ Heure</th>'
            for day in DAYS:
                date_lbl = (f"<span class='day-date'>{_day_dates[day]}</span>")
                html += f'<th>{day}{date_lbl}</th>'
            html += '</tr></thead><tbody>'

            for (start, end) in time_slots:
                html += (f'<tr><td class="time-td">'
                         f'<span style="color:#1E293B;font-size:0.80rem">{start}</span>'
                         f'<br><span style="color:#CBD5E1;font-size:0.58rem">▼</span>'
                         f'<br><span style="color:#1E293B;font-size:0.80rem">{end}</span>'
                         f'</td>')
                for day in DAYS:
                    html += '<td>'
                    for s in grid[(start, end)][day]:
                        _st     = s.get("slot_type") or "cours"
                        _rm     = s.get("room") or "—"
                        _status = s.get("slot_status") or "actif"
                        _sub    = s.get("substitute_name")
                        _pdisp  = (_sub or s.get("professor_name", ""))
                        _opac   = "0.42" if _status == "annule" else "1"
                        _xstyle = f"opacity:{_opac};"
                        _ini    = _av_init(_pdisp)
                        if _st == "ferie":
                            html += (
                                f'<div class="slot slot-ferie" style="{_xstyle}">'
                                f'<div class="sn sn-ferie">🚫 {s["course_name"]}</div>'
                                f'<span class="slot-type-badge badge-ferie">Férié</span>'
                                f'</div>'
                            )
                        elif _st == "examen":
                            _av = (f'<span class="prof-av prof-av-examen">{_ini}</span>'
                                   if _pdisp else "")
                            html += (
                                f'<div class="slot slot-examen" style="{_xstyle}">'
                                f'<div class="sn sn-examen">📝 {s["course_name"]}</div>'
                                f'<div class="sp sp-examen">{_av}{_pdisp}</div>'
                                f'<div class="sr sr-examen">🏛 {_rm}</div>'
                                f'<span class="slot-type-badge badge-examen">Examen</span>'
                                f'</div>'
                            )
                        else:
                            _sbadge = ""
                            if _status == "annule":
                                _sbadge = '<span class="slot-type-badge" style="background:#FEE2E2;color:#991B1B">ANNULÉ</span>'
                            elif _status == "remplace":
                                _sbadge = '<span class="slot-type-badge" style="background:#FEF3C7;color:#92400E">REMPLACÉ</span>'
                            _av = (f'<span class="prof-av prof-av-cours">{_ini}</span>'
                                   if _pdisp else "")
                            _sub_pfx = "🔄 " if _sub else ""
                            html += (
                                f'<div class="slot slot-cours" style="{_xstyle}">'
                                f'<div class="sn sn-cours">{s["course_name"]}</div>'
                                f'<div class="sp sp-cours">{_av}{_sub_pfx}{_pdisp}</div>'
                                f'<div class="sr sr-cours">📍 {_rm}</div>'
                                f'{_sbadge}'
                                f'</div>'
                            )
                    html += '</td>'
                html += '</tr>'
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

        # ── iCal export ───────────────────────────────────────────────────────
        try:
            from utils.ical_export import generate_ical as _gen_ical
            _ics = _gen_ical(schedules, cls["name"], uni_name)
            st.download_button(
                "📅 Exporter vers Google Calendar / iCal",
                data=_ics,
                file_name=f"EDT_{cls['name'].replace(' ', '_')}.ics",
                mime="text/calendar",
                use_container_width=True,
            )
        except Exception as _ical_err:
            st.caption(f"Export iCal indisponible : {_ical_err}")

# ── ONGLET 2 : COURS ──────────────────────────────────────────────────────────
with tab_c:
    if not courses:
        st.info("📭 Aucun cours pour cette classe.")
    else:
        total_h = sum(c.get("hours", 0) for c in courses)
        m1, m2 = st.columns(2)
        m1.metric("Nombre de matières", len(courses))
        m2.metric("Volume horaire", f"{total_h}h")
        st.divider()
        for c in courses:
            code_str = f"[{c['code']}] " if c.get("code") else ""
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:0.7rem 1.1rem;background:white;
                        border:1px solid #E8EFF8;border-left:3px solid #2563EB;
                        border-radius:10px;margin-bottom:0.45rem;
                        box-shadow:0 1px 4px rgba(0,0,0,0.04);
                        transition:box-shadow 0.15s">
                <span style="font-weight:600;color:#1E293B;font-size:0.88rem">{code_str}{c['name']}</span>
                <div style="display:flex;gap:0.75rem;font-size:0.80rem">
                    <span style="background:#EFF6FF;color:#1D4ED8;padding:2px 8px;
                                 border-radius:999px;font-weight:600">⏱ {c.get('hours',0)}h</span>
                    <span style="background:#F5F3FF;color:#5B21B6;padding:2px 8px;
                                 border-radius:999px;font-weight:600">×{c.get('weight',1.0)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── ONGLET 3 : PROFESSEURS ────────────────────────────────────────────────────
with tab_p:
    if not professors:
        st.info("📭 Aucun professeur enregistré.")
    else:
        cols = st.columns(2, gap="medium")
        for i, p in enumerate(professors):
            with cols[i % 2]:
                from utils.components import _initials as _pav
                _pini = _pav(p['name'])
                email_str = f"✉️ {p['email']}" if p.get("email") else "—"
                phone_str = f" · 📞 {p['phone']}" if p.get("phone") else ""
                st.markdown(f"""
                <div style="background:white;border:1px solid #E8EFF8;border-radius:12px;
                            padding:0.9rem 1.1rem;margin-bottom:0.6rem;
                            display:flex;align-items:center;gap:0.85rem;
                            box-shadow:0 2px 8px rgba(0,0,0,0.04);
                            transition:box-shadow 0.15s,transform 0.15s">
                    <div style="width:44px;height:44px;border-radius:50%;flex-shrink:0;
                                background:linear-gradient(135deg,#2563EB,#3B82F6);
                                display:flex;align-items:center;justify-content:center;
                                color:white;font-size:0.85rem;font-weight:700;
                                box-shadow:0 2px 8px rgba(37,99,235,0.30)">{_pini}</div>
                    <div>
                        <div style="font-weight:700;color:#1E293B;font-size:0.88rem">{p['name']}</div>
                        <div style="color:#94A3B8;font-size:0.74rem;margin-top:2px">{email_str}{phone_str}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ── ONGLET 4 : COMMUNIQUÉS ────────────────────────────────────────────────────
with tab_a:
    if not announcements:
        st.info("📭 Aucun communiqué pour ce département.")
    else:
        for ann in announcements:
            announcement_card(ann)
