# pages/2_Horaire.py
import streamlit as st
from db.queries import (FacultyQueries, DepartmentQueries, PromotionQueries,
                        ClassQueries, ScheduleQueries, CourseQueries,
                        ProfessorQueries, AnnouncementQueries, UniversityQueries)
from utils.components import inject_global_css, announcement_card
from datetime import timedelta, time as dt_time

inject_global_css()

st.markdown("""
<style>
    .selectors-bar {
        background: white; border: 1px solid #E2E8F0;
        border-radius: 14px; padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .sched-wrap { overflow-x: auto; }
    table.sched {
        width: 100%; border-collapse: collapse;
        font-size: 0.8rem; font-family: 'Inter', sans-serif;
    }
    table.sched th {
        background: #1E40AF; color: white;
        padding: 10px 14px; text-align: center;
        font-weight: 600; letter-spacing: 0.03em;
        border: 1px solid #1D4ED8;
    }
    table.sched th.time-th { background: #0F172A; width: 100px; }
    table.sched td {
        border: 1px solid #E2E8F0; vertical-align: top;
        padding: 4px; min-width: 110px; height: 64px; background: #FAFAFA;
    }
    table.sched td.time-td {
        background: #F1F5F9; text-align: center;
        font-weight: 600; color: #475569; font-size: 0.75rem;
        vertical-align: middle;
    }
    .slot {
        background: #EFF6FF; border-left: 3px solid #2563EB;
        border-radius: 5px; padding: 5px 7px; margin: 2px;
    }
    .slot .sn { font-weight:700; color:#1E40AF; font-size:0.78rem; }
    .slot .sp { color:#64748B; font-size:0.72rem; margin-top:2px; }
    .slot .sr { color:#0EA5E9; font-size:0.68rem; }
    .class-banner {
        background: linear-gradient(90deg, #1E40AF, #2563EB);
        color: white; border-radius: 10px;
        padding: 0.75rem 1.25rem;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 1.25rem;
    }
    .class-banner h3 { margin:0; font-family:'Poppins',sans-serif; font-size:1.1rem; }
    .class-banner span { font-size:0.82rem; opacity:0.85; }
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


# ── FIX 2 : Navigation directe (sidebar) sans université pré-sélectionnée ────
uni_id   = st.session_state.get("sel_uni_id")
uni_name = st.session_state.get("sel_uni_name", "")

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
except Exception as e:
    st.error(f"❌ Erreur chargement données : {e}"); st.stop()

# ── Bannière classe ───────────────────────────────────────────────────────────
promo_label = promo_sel_name.split(" (")[0]
st.markdown(f"""
<div class="class-banner">
    <h3>🏫 Classe {cls['name']} &nbsp;·&nbsp; {promo_label}</h3>
    <span>{dept['name']} · {fac['name']}</span>
</div>
""", unsafe_allow_html=True)

# ── Onglets ───────────────────────────────────────────────────────────────────
tab_h, tab_c, tab_p, tab_a = st.tabs([
    "📅 Emploi du Temps",
    f"📘 Cours ({len(courses)})",
    f"👨‍🏫 Professeurs ({len(professors)})",
    f"📢 Communiqués ({len(announcements)})",
])

# ── ONGLET 1 : GRILLE HORAIRE ─────────────────────────────────────────────────
with tab_h:
    col_f, _ = st.columns([2, 5])
    with col_f:
        week_filter = st.radio("Semaine :", ["Toutes", "Paire", "Impaire"],
                               horizontal=True, key="wf")

    filtered = schedules if week_filter == "Toutes" else \
               [s for s in schedules if s.get("week_type") in ("Toutes", week_filter)]

    if not filtered:
        st.info("📭 Aucun cours planifié pour cette classe.")
    else:
        DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

        # FIX 2 : Utilise fmt_time() pour gérer TIME et timedelta
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

        html  = '<div class="sched-wrap"><table class="sched"><thead><tr>'
        html += '<th class="time-th">⏱ Horaire</th>'
        for day in DAYS:
            html += f'<th>{day}</th>'
        html += '</tr></thead><tbody>'

        for (start, end) in time_slots:
            html += f'<tr><td class="time-td">{start}<br>↓<br>{end}</td>'
            for day in DAYS:
                html += '<td>'
                for s in grid[(start, end)][day]:
                    room = s.get("room") or "—"
                    html += f"""
                    <div class="slot">
                        <div class="sn">{s['course_name']}</div>
                        <div class="sp">👤 {s['professor_name']}</div>
                        <div class="sr">📍 {room}</div>
                    </div>"""
                html += '</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)

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
            code_str = f"[{c['code']}]" if c.get("code") else ""
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:0.65rem 1rem;background:white;border:1px solid #E2E8F0;
                        border-radius:10px;margin-bottom:0.5rem">
                <span style="font-weight:600;color:#1E293B">{code_str} {c['name']}</span>
                <div style="display:flex;gap:1rem;font-size:0.82rem;color:#64748B">
                    <span>⏱ {c.get('hours',0)}h</span>
                    <span>Coeff. {c.get('weight',1.0)}</span>
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
                email_str = f"✉️ {p['email']}" if p.get("email") else ""
                phone_str = f"📞 {p['phone']}" if p.get("phone") else ""
                st.markdown(f"""
                <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;
                            padding:0.85rem 1.1rem;margin-bottom:0.75rem;
                            display:flex;align-items:center;gap:0.75rem">
                    <div style="width:42px;height:42px;border-radius:50%;
                                background:linear-gradient(135deg,#2563EB,#0EA5E9);
                                display:flex;align-items:center;justify-content:center;
                                color:white;font-size:1.1rem;flex-shrink:0">👤</div>
                    <div>
                        <div style="font-weight:600;color:#1E293B;font-size:0.9rem">{p['name']}</div>
                        <div style="color:#94A3B8;font-size:0.76rem">{email_str} {phone_str}</div>
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
