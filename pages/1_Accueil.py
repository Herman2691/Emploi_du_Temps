# pages/1_Accueil.py
import streamlit as st
from db.queries import UniversityQueries
from utils.components import inject_global_css

inject_global_css()

# Déterminer l'université de l'utilisateur connecté (admin/prof ou étudiant)
_conn_uni_id = None
if st.session_state.get("authenticated") and st.session_state.get("user"):
    _conn_uni_id = st.session_state["user"].get("university_id")
elif st.session_state.get("student_authenticated") and st.session_state.get("student"):
    _conn_uni_id = st.session_state["student"].get("university_id")

st.markdown("""
<style>
/* ── Hero ──────────────────────────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #0A0F1E 0%, #0F172A 40%, #1A2744 70%, #0F2340 100%);
    border-radius: 22px;
    padding: 3.75rem 2.5rem;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse at 75% 45%, rgba(37,99,235,0.30) 0%, transparent 58%),
        radial-gradient(ellipse at 20% 75%, rgba(16,185,129,0.18) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 10%, rgba(124,58,237,0.12) 0%, transparent 45%);
    pointer-events: none;
}
.hero::after {
    content: "";
    position: absolute; inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
}
.hero h1 {
    font-family: 'Poppins', sans-serif;
    font-size: 2.9rem; font-weight: 800;
    margin: 0; line-height: 1.12;
    background: linear-gradient(135deg, #ffffff 20%, #93C5FD 70%, #A78BFA 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative; z-index: 1;
}
.hero .subtitle {
    font-size: 1.05rem; opacity: 0.72;
    margin: 0.85rem 0 0; max-width: 540px;
    margin-left: auto; margin-right: auto;
    line-height: 1.65; position: relative; z-index: 1;
}
.hero-badge {
    display: inline-block;
    background: rgba(37,99,235,0.25); border: 1px solid rgba(99,155,255,0.35);
    border-radius: 30px; padding: 0.28rem 1rem;
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.09em; text-transform: uppercase;
    color: #93C5FD; margin-bottom: 1.3rem;
    position: relative; z-index: 1;
    backdrop-filter: blur(4px);
}

/* ── Features ───────────────────────────────────────────────────────────── */
.feature-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.5rem 1.25rem;
    text-align: center;
    height: 100%;
    transition: all 0.2s ease;
}
.feature-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    transform: translateY(-3px);
    border-color: #BFDBFE;
}
.feature-card .icon {
    font-size: 2.2rem; margin-bottom: 0.75rem;
}
.feature-card h4 {
    font-family: 'Poppins', sans-serif;
    font-size: 0.95rem; font-weight: 700;
    color: #1E293B; margin: 0 0 0.4rem;
}
.feature-card p {
    font-size: 0.82rem; color: #64748B;
    margin: 0; line-height: 1.55;
}

/* ── Stats ──────────────────────────────────────────────────────────────── */
.stats-bar {
    background: linear-gradient(135deg, #1E40AF, #2563EB);
    border-radius: 14px;
    padding: 1.25rem 2rem;
    display: flex; justify-content: space-around; align-items: center;
    margin: 1.5rem 0;
    flex-wrap: wrap; gap: 1rem;
}
.stat-item { text-align: center; color: white; }
.stat-item .num {
    font-family: 'Poppins', sans-serif;
    font-size: 2rem; font-weight: 800; line-height: 1;
}
.stat-item .lbl { font-size: 0.78rem; opacity: 0.8; margin-top: 0.2rem; }

/* ── Section title ───────────────────────────────────────────────────────── */
.section-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.3rem; font-weight: 700;
    color: #1E293B; margin: 0 0 0.25rem;
}
.section-sub { color: #64748B; font-size: 0.875rem; margin: 0 0 1.25rem; }

/* ── Carte université ────────────────────────────────────────────────────── */
.uni-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.22s ease;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.uni-card:hover {
    box-shadow: 0 10px 32px rgba(0,0,0,0.11);
    transform: translateY(-4px);
    border-color: #BFDBFE;
}
.uni-card-cover {
    width: 100%; height: 130px; object-fit: cover; display: block;
}
.uni-card-cover-fallback {
    width: 100%; height: 130px;
    display: flex; align-items: center; justify-content: center;
    font-size: 3rem;
}
.uni-card-body { padding: 0.9rem 1.1rem 0.8rem; }
.uni-card-body h4 {
    font-family: 'Poppins', sans-serif;
    font-size: 0.92rem; font-weight: 700;
    margin: 0 0 0.25rem; color: #1E293B; line-height: 1.3;
}
.uni-card-body p  { margin: 0; color: #64748B; font-size: 0.78rem; }
.uni-color-bar { height: 4px; width: 100%; }

/* ── CTA Institutions ────────────────────────────────────────────────────── */
.cta-card {
    background: linear-gradient(135deg, #F8FAFC, #EFF6FF);
    border: 1px dashed #CBD5E1;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    text-align: center;
    margin-top: 1.5rem;
}
.cta-card h3 {
    font-family: 'Poppins', sans-serif;
    font-size: 1.2rem; font-weight: 700;
    color: #1E293B; margin: 0 0 0.5rem;
}
.cta-card p { color: #64748B; font-size: 0.875rem; margin: 0 0 1.25rem; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-badge">Plateforme académique</div>
    <h1>🎓 UniSchedule</h1>
    <p class="subtitle">
        Consultez votre emploi du temps, déposez vos TPs, suivez vos notes
        — le tout sans installation, accessible depuis n'importe quel appareil.
    </p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# FONCTIONNALITÉS
# ════════════════════════════════════════════════════════════════════════════
f1, f2, f3, f4 = st.columns(4, gap="medium")

features = [
    ("📅", "Emploi du temps", "Horaires en temps réel, filtre semaines paires / impaires, grille hebdomadaire claire."),
    ("📝", "Travaux pratiques", "Déposez vos TPs en PDF avant la deadline. Le dépôt se ferme automatiquement."),
    ("📊", "Notes & résultats", "Vos résultats publiés directement par vos professeurs, classés par matière."),
    ("📄", "Cours en PDF", "Téléchargez les documents de cours déposés par vos enseignants, à tout moment."),
]

for col, (icon, title, desc) in zip([f1, f2, f3, f4], features):
    with col:
        st.markdown(f"""
        <div class="feature-card">
            <div class="icon">{icon}</div>
            <h4>{title}</h4>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# BARRE DE STATS
# ════════════════════════════════════════════════════════════════════════════
if _conn_uni_id:
    try:
        from db.connection import execute_query as _eq_acc
        _s = _eq_acc("""
            SELECT
                (SELECT COUNT(*) FROM professors WHERE university_id=%s AND is_active=TRUE) AS prof_count,
                (SELECT COUNT(*) FROM schedules sch
                 JOIN courses c ON sch.course_id=c.id
                 JOIN promotions pr ON c.promotion_id=pr.id
                 JOIN departments d ON pr.department_id=d.id
                 JOIN faculties f ON d.faculty_id=f.id
                 WHERE f.university_id=%s AND sch.is_active=TRUE) AS schedule_count,
                (SELECT COUNT(*) FROM students WHERE university_id=%s AND is_active=TRUE) AS student_count,
                (SELECT COUNT(*) FROM departments d
                 JOIN faculties f ON d.faculty_id=f.id
                 WHERE f.university_id=%s AND d.is_active=TRUE) AS dept_count
        """, (_conn_uni_id,)*4, fetch="one") or {}
    except Exception:
        _s = {}
    prof_count = _s.get("prof_count", 0)
    sch_count  = _s.get("schedule_count", 0)
    stu_count  = _s.get("student_count", 0)
    dept_count = _s.get("dept_count", 0)
    st.markdown(f"""
<div class="stats-bar">
    <div class="stat-item"><div class="num">{dept_count}</div><div class="lbl">Département(s)</div></div>
    <div class="stat-item"><div class="num">{prof_count}</div><div class="lbl">Professeurs</div></div>
    <div class="stat-item"><div class="num">{sch_count}</div><div class="lbl">Créneaux planifiés</div></div>
    <div class="stat-item"><div class="num">{stu_count}</div><div class="lbl">Étudiants inscrits</div></div>
</div>
""", unsafe_allow_html=True)
else:
    try:
        stats = UniversityQueries.get_platform_stats() or {}
    except Exception:
        stats = {}
    uni_count  = stats.get("uni_count", 0)
    prof_count = stats.get("prof_count", 0)
    sch_count  = stats.get("schedule_count", 0)
    stu_count  = stats.get("student_count", 0)
    st.markdown(f"""
<div class="stats-bar">
    <div class="stat-item"><div class="num">{uni_count}</div><div class="lbl">Université(s)</div></div>
    <div class="stat-item"><div class="num">{prof_count}</div><div class="lbl">Professeurs</div></div>
    <div class="stat-item"><div class="num">{sch_count}</div><div class="lbl">Créneaux planifiés</div></div>
    <div class="stat-item"><div class="num">{stu_count}</div><div class="lbl">Étudiants inscrits</div></div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# LISTE DES UNIVERSITÉS
# ════════════════════════════════════════════════════════════════════════════
if _conn_uni_id:
    st.markdown("""
<p class="section-title">🏛️ Votre université</p>
<p class="section-sub">Accédez directement à l'emploi du temps de votre établissement</p>
""", unsafe_allow_html=True)
else:
    st.markdown("""
<p class="section-title">🏛️ Choisissez votre université</p>
<p class="section-sub">Sélectionnez votre établissement pour accéder à votre emploi du temps</p>
""", unsafe_allow_html=True)

try:
    universities = UniversityQueries.get_all()
except Exception as e:
    st.error(f"❌ Connexion impossible : {e}")
    st.info("💡 Configurez `.streamlit/secrets.toml`")
    st.stop()

if _conn_uni_id:
    universities = [u for u in universities if u["id"] == _conn_uni_id]
else:
    search = st.text_input(
        "", placeholder="🔍  Rechercher une université...",
        label_visibility="collapsed"
    )
    if search:
        universities = [
            u for u in universities
            if search.lower() in u["name"].lower()
            or (u.get("address") and search.lower() in u["address"].lower())
        ]

if not universities:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#94A3B8">
        <div style="font-size:3rem">🏛️</div>
        <p>Aucune université trouvée.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    cols = st.columns(3, gap="medium")
    for i, uni in enumerate(universities):
        with cols[i % 3]:
            _raw_photo = uni.get("photo_url") or ""
            if _raw_photo and not _raw_photo.startswith("http"):
                from utils.components import get_logo_display_url
                _raw_photo = get_logo_display_url(_raw_photo) or ""
            photo = _raw_photo or "https://images.unsplash.com/photo-1562774053-701939374585?w=400"
            address = uni.get("address") or "—"
            color   = uni.get("primary_color") or "#2563EB"

            if _raw_photo:
                _cover_html = f'<img class="uni-card-cover" src="{_raw_photo}" alt="{uni["name"]}">'
            else:
                _cover_html = (f'<div class="uni-card-cover-fallback" '
                               f'style="background:linear-gradient(135deg,{color}18,{color}30)">🏛️</div>')
            st.markdown(f"""
            <div class="uni-card" style="border-top:4px solid {color}">
                {_cover_html}
                <div class="uni-card-body">
                    <h4 style="color:{color}">{uni['name']}</h4>
                    <p>📍 {address}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(
                "Voir l'horaire →",
                key=f"uni_{uni['id']}",
                use_container_width=True,
                type="primary",
            ):
                st.session_state["sel_uni_id"]   = uni["id"]
                st.session_state["sel_uni_name"] = uni["name"]
                st.switch_page("pages/2_Horaire.py")

    st.caption(f"{len(universities)} université(s) disponible(s)")


# ════════════════════════════════════════════════════════════════════════════
# CTA INSTITUTIONS (masqué si connecté)
# ════════════════════════════════════════════════════════════════════════════
if not _conn_uni_id:
    st.markdown("""
<div class="cta-card">
    <h3>📣 Votre université n'est pas encore sur UniSchedule ?</h3>
    <p>
        Rejoignez la plateforme et offrez à vos étudiants un accès simple
        à leurs emplois du temps, TPs et notes.
    </p>
</div>
""", unsafe_allow_html=True)

    _, cta_col, _ = st.columns([1, 2, 1])
    with cta_col:
        st.link_button(
            "✉️ Nous contacter pour rejoindre la plateforme",
            "mailto:contact@unischedule.dz",
            use_container_width=True,
        )
