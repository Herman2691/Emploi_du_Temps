# utils/components.py
import streamlit as st
from datetime import datetime, timedelta, time as dt_time


def fmt_time(t) -> str:
    """Convertit datetime.time ou timedelta (psycopg2) → 'HH:MM'."""
    if t is None:
        return "--:--"
    if isinstance(t, timedelta):
        total = int(t.total_seconds())
        h, m  = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    if isinstance(t, dt_time):
        return t.strftime("%H:%M")
    return str(t)[:5]


def get_logo_display_url(photo_url: str) -> str | None:
    """Returns a displayable URL for a university logo (external URL or base64 data URI)."""
    if not photo_url:
        return None
    if photo_url.startswith("http://") or photo_url.startswith("https://"):
        return photo_url
    try:
        from utils.storage import get_file_base64
        return get_file_base64(photo_url)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Tokens, composants Streamlit, classes globales
# ══════════════════════════════════════════════════════════════════════════════

def inject_global_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
#MainMenu, footer { visibility: hidden; }

/* ── Tokens ─────────────────────────────────────────────────────────────── */
:root {
    --blue-50:#EFF6FF; --blue-100:#DBEAFE; --blue-600:#2563EB;
    --blue-700:#1D4ED8; --blue-800:#1E40AF;
    --em-50:#ECFDF5;   --em-600:#059669;   --em-700:#047857;
    --vi-50:#F5F3FF;   --vi-600:#7C3AED;   --vi-700:#6D28D9;
    --am-50:#FFFBEB;   --am-500:#F59E0B;
    --rd-50:#FEF2F2;   --rd-500:#EF4444;
    --cy-500:#06B6D4;

    --sl-50:#F8FAFC;  --sl-100:#F1F5F9;  --sl-200:#E2E8F0;
    --sl-300:#CBD5E1; --sl-400:#94A3B8;  --sl-500:#64748B;
    --sl-600:#475569; --sl-700:#334155;  --sl-800:#1E293B;  --sl-900:#0F172A;

    --border: #E2E8F0;
    --r-sm:6px; --r-md:10px; --r-lg:14px; --r-xl:20px; --r-full:9999px;
    --sh-sm: 0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
    --sh-md: 0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    --sh-lg: 0 10px 32px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.05);
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: white !important;
    border-right: 1px solid var(--sl-100) !important;
    box-shadow: 2px 0 16px rgba(0,0,0,0.05) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem !important; }

/* ── Sidebar text — force couleurs identiques desktop ET mobile ─────────── */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarNav"] {
    background: white !important;
    color: #1E293B !important;
    -webkit-text-fill-color: #1E293B !important;
}
[data-testid="stSidebarNavLink"] p,
[data-testid="stSidebarNavLink"] span,
[data-testid="stSidebarNavLink"] div {
    color: #334155 !important;
    -webkit-text-fill-color: #334155 !important;
}
[data-testid="stSidebarNavLink"]:hover p,
[data-testid="stSidebarNavLink"]:hover span {
    color: #1E293B !important;
    -webkit-text-fill-color: #1E293B !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] p,
[data-testid="stSidebarNavLink"][aria-current="page"] span {
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    font-weight: 600 !important;
}
[data-testid="stSidebarNavSeparator"] span,
[data-testid="stSidebarNavSeparator"] p {
    color: #94A3B8 !important;
    -webkit-text-fill-color: #94A3B8 !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* ── Mobile : identique desktop ─────────────────────────────────────────── */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        background: white !important;
    }
    [data-testid="stSidebar"] * {
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
    }
    [data-testid="stSidebarNavLink"] p,
    [data-testid="stSidebarNavLink"] span {
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] p,
    [data-testid="stSidebarNavLink"][aria-current="page"] span {
        color: #2563EB !important;
        -webkit-text-fill-color: #2563EB !important;
    }
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
}
.main .block-container { padding-top: 1.25rem !important; padding-bottom: 2rem !important; }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
    background: var(--sl-100) !important;
    border-radius: var(--r-lg) !important;
    padding: 4px !important;
    gap: 2px !important;
    margin-bottom: 1rem !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--r-md) !important;
    padding: 0.45rem 1rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: var(--sl-500) !important;
    border: none !important;
    transition: all 0.15s ease !important;
}
[data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.85) !important;
    color: var(--sl-700) !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: white !important;
    color: var(--blue-600) !important;
    font-weight: 600 !important;
    box-shadow: var(--sh-sm) !important;
}
[data-baseweb="tab-border"],
[data-baseweb="tab-highlight"] { display: none !important; }

/* ── Expander ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--sl-200) !important;
    border-radius: var(--r-lg) !important;
    margin-bottom: 0.5rem !important;
    overflow: hidden !important;
    background: white !important;
    box-shadow: var(--sh-sm) !important;
    transition: box-shadow 0.15s !important;
}
[data-testid="stExpander"]:hover { box-shadow: var(--sh-md) !important; }
[data-testid="stExpander"] summary {
    padding: 0.875rem 1rem !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--sl-700) !important;
}
[data-testid="stExpander"] summary:hover { background: var(--sl-50) !important; }
[data-testid="stExpander"] > div > div { padding: 0 1rem 0.75rem !important; }

/* ── Metric ──────────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid var(--sl-200) !important;
    border-radius: var(--r-lg) !important;
    padding: 1.1rem 1.25rem !important;
    box-shadow: var(--sh-sm) !important;
    transition: box-shadow 0.15s, transform 0.15s !important;
}
[data-testid="metric-container"]:hover {
    box-shadow: var(--sh-md) !important;
    transform: translateY(-2px) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.75rem !important;
    color: var(--blue-600) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    color: var(--sl-500) !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Form controls ───────────────────────────────────────────────────────── */
[data-testid="stTextInput"] > div > div > input,
[data-testid="stTextArea"] > div > div > textarea {
    border: 1px solid var(--sl-200) !important;
    border-radius: var(--r-md) !important;
    font-size: 0.875rem !important;
    background: white !important;
    color: var(--sl-800) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stTextInput"] > div > div > input:focus,
[data-testid="stTextArea"] > div > div > textarea:focus {
    border-color: var(--blue-600) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.10) !important;
    outline: none !important;
}
[data-testid="stSelectbox"] > div > div {
    border: 1px solid var(--sl-200) !important;
    border-radius: var(--r-md) !important;
    transition: border-color 0.15s !important;
}
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed var(--sl-300) !important;
    border-radius: var(--r-lg) !important;
    background: var(--sl-50) !important;
    transition: all 0.15s !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--blue-600) !important;
    background: var(--blue-50) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
[data-testid="stButton"] > button {
    border-radius: var(--r-md) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, var(--blue-600), var(--blue-700)) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--blue-700), var(--blue-800)) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;
}
[data-testid="stButton"] > button[kind="primary"]:active { transform: translateY(0) !important; }
[data-testid="stButton"] > button[kind="secondary"] {
    border: 1px solid var(--sl-200) !important;
    color: var(--sl-600) !important;
    background: white !important;
}
[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: var(--sl-300) !important;
    background: var(--sl-50) !important;
    color: var(--sl-800) !important;
}

/* ── Alerts ──────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--r-md) !important;
    font-size: 0.875rem !important;
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr { border-color: var(--sl-200) !important; margin: 0.75rem 0 !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--sl-300); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--sl-400); }

/* ══ CLASSES RÉUTILISABLES ════════════════════════════════════════════════ */

.uni-card {
    background: white; border: 1px solid var(--sl-200);
    border-radius: var(--r-lg); padding: 1.25rem; margin-bottom: 0.75rem;
    box-shadow: var(--sh-sm); transition: all 0.15s ease;
}
.uni-card:hover {
    border-color: var(--blue-600); box-shadow: var(--sh-md); transform: translateY(-2px);
}
.uni-card h3 { color: var(--sl-800); margin: 0.5rem 0 0.25rem; font-family: 'Poppins', sans-serif; }
.uni-card p  { color: var(--sl-500); font-size: 0.875rem; margin: 0; }

.stat-card {
    background: white; border: 1px solid var(--sl-200);
    border-radius: var(--r-lg); padding: 1.125rem 1.25rem;
    text-align: center; box-shadow: var(--sh-sm);
    transition: box-shadow 0.15s, transform 0.15s; height: 100%;
}
.stat-card:hover { box-shadow: var(--sh-md); transform: translateY(-2px); }
.stat-card .s-icon { font-size: 1.4rem; margin-bottom: 0.35rem; }
.stat-card .s-value {
    font-size: 1.875rem; font-weight: 800;
    font-family: 'Poppins', sans-serif;
    color: var(--blue-600); line-height: 1;
}
.stat-card .s-label {
    color: var(--sl-500); font-size: 0.72rem; font-weight: 600;
    margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.05em;
}

.badge {
    display: inline-flex; align-items: center;
    padding: 0.18rem 0.65rem; border-radius: var(--r-full);
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.02em; line-height: 1.4;
}
.badge-super    { background: #FEF3C7; color: #92400E; }
.badge-univ     { background: var(--blue-100); color: var(--blue-800); }
.badge-fac      { background: var(--em-50);    color: #065F46; }
.badge-dept     { background: var(--vi-50);    color: #4C1D95; }
.badge-active   { background: #DCFCE7; color: #15803D; }
.badge-inactive { background: #FEE2E2; color: #DC2626; }
.badge-info     { background: var(--blue-50);  color: var(--blue-800); }
.badge-warn     { background: var(--am-50);    color: #92400E; }

.announcement {
    border-left: 3px solid var(--blue-600); background: var(--blue-50);
    padding: 0.875rem 1rem;
    border-radius: 0 var(--r-md) var(--r-md) 0; margin-bottom: 0.75rem;
}
.announcement.pinned { border-left-color: var(--am-500); background: var(--am-50); }
.announcement h4 {
    margin: 0 0 0.3rem; color: var(--sl-800); font-size: 0.9rem; font-weight: 600;
}
.announcement p {
    margin: 0; color: var(--sl-600); font-size: 0.82rem; line-height: 1.55;
}

.section-header {
    display: flex; align-items: center; gap: 0.5rem;
    border-bottom: 2px solid var(--sl-200);
    padding-bottom: 0.5rem; margin-bottom: 1rem;
}
.section-header h2 {
    margin: 0; font-family: 'Poppins', sans-serif;
    color: var(--sl-800); font-size: 1.35rem; font-weight: 700;
}

.empty-state { text-align: center; padding: 2.5rem 1rem; }
.empty-state .es-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-state .es-text { font-size: 0.9rem; color: var(--sl-500); margin: 0; }
.empty-state .es-sub  { font-size: 0.78rem; color: var(--sl-400); margin-top: 0.3rem; }

/* ── Grille horaire ──────────────────────────────────────────────────────── */
.sched-wrap {
    overflow-x: auto; border-radius: var(--r-lg);
    border: 1px solid var(--sl-200);
    box-shadow: 0 4px 20px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.04);
    margin-top: 0.75rem; background: white;
}
.sched {
    width: 100%; border-collapse: collapse;
    font-size: 0.8rem; min-width: 720px;
}
.sched thead th {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    color: rgba(255,255,255,0.95);
    padding: 12px 14px; text-align: center;
    font-weight: 600; font-size: 0.79rem;
    border: 1px solid #2D3A4A;
    position: sticky; top: 0; z-index: 2;
    letter-spacing: 0.03em;
}
.sched thead th.time-th {
    background: #0F172A; width: 90px;
    font-size: 0.67rem; text-transform: uppercase;
    letter-spacing: 0.08em;
}
.sched tbody td {
    border: 1px solid #EEF2F8;
    padding: 5px; vertical-align: top;
    min-width: 120px; background: #FAFBFF;
}
.sched tbody td.time-td {
    background: linear-gradient(180deg, #F8FAFC, #F1F5F9);
    font-weight: 700; color: var(--sl-500);
    text-align: center; font-size: 0.73rem;
    vertical-align: middle; padding: 6px 4px;
    min-width: 0; width: 90px; line-height: 1.5;
    border-right: 2px solid #E2E8F0;
}
.sched tbody tr:hover td:not(.time-td) { background: #F2F7FF; }

/* ── Slot cards ──────────────────────────────────────────────────────────── */
.slot {
    border-radius: 8px; padding: 7px 9px; margin: 3px;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    cursor: default;
}
.slot:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(0,0,0,0.10) !important;
}
.slot-cours {
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    border: 1px solid #BFDBFE; border-left: 4px solid #2563EB;
}
.slot-examen {
    background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
    border: 1px solid #A7F3D0; border-left: 4px solid #059669;
}
.slot-ferie {
    background: linear-gradient(135deg, #FFF7ED 0%, #FEE2E2 100%);
    border: 1px solid #FCA5A5; border-left: 4px solid #DC2626;
}

/* ── Texte des slots ─────────────────────────────────────────────────────── */
.sn { font-weight: 700; font-size: 0.79rem; line-height: 1.3; }
.sn-cours  { color: #1E40AF; }
.sn-examen { color: #065F46; }
.sn-ferie  { color: #991B1B; }
.sp { font-size: 0.70rem; margin-top: 4px; display: flex; align-items: center; gap: 4px; }
.sp-cours  { color: #475569; }
.sp-examen { color: #065F46; }
.sr { font-size: 0.68rem; margin-top: 3px; }
.sr-cours  { color: #0891B2; }
.sr-examen { color: #059669; }

/* ── Avatar initiales professeur ─────────────────────────────────────────── */
.prof-av {
    display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px; border-radius: 50%;
    font-size: 0.52rem; font-weight: 700; flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.7);
}
.prof-av-cours  { background: linear-gradient(135deg,#2563EB,#3B82F6); color:white; }
.prof-av-examen { background: linear-gradient(135deg,#059669,#10B981); color:white; }

/* ── Badges type/statut ──────────────────────────────────────────────────── */
.slot-type-badge {
    display: inline-block; font-size: 0.58rem; font-weight: 700;
    padding: 1px 5px; border-radius: 3px; margin-top: 4px;
    letter-spacing: 0.07em; text-transform: uppercase;
}
.badge-examen { background: #DCFCE7; color: #065F46; }
.badge-ferie  { background: #FEE2E2; color: #991B1B; }
.day-date { font-size: 0.63rem; font-weight: 400; opacity: 0.68; display: block; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH PAGES — CSS partagé (élimine la triplication entre les 3 pages login)
# ══════════════════════════════════════════════════════════════════════════════

def auth_page_css(accent: str = "#2563EB", accent_dark: str = "#1D4ED8") -> str:
    """Retourne le CSS complet pour les pages d'authentification (thème clair)."""
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {{ display: none !important; }}
#MainMenu, footer, header {{ visibility: hidden !important; }}

.stApp {{
    background: linear-gradient(160deg, #F8FAFC 0%, #EFF6FF 55%, #F0FDF4 100%) !important;
    min-height: 100vh;
}}

/* ── Inputs ── */
[data-testid="stTextInput"] > div > div > input {{
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    color: #1E293B !important; border-radius: 10px !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    -webkit-text-fill-color: #1E293B !important;
}}
[data-testid="stTextInput"] > div > div > input::placeholder {{ color: #CBD5E1 !important; }}
[data-testid="stTextInput"] > div > div > input:-webkit-autofill,
[data-testid="stTextInput"] > div > div > input:-webkit-autofill:hover,
[data-testid="stTextInput"] > div > div > input:-webkit-autofill:focus {{
    -webkit-text-fill-color: #1E293B !important;
    -webkit-box-shadow: 0 0 0px 1000px white inset !important;
    transition: background-color 5000s ease-in-out 0s;
}}
[data-testid="stTextInput"] > div > div > input:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 3px {accent}18 !important;
    outline: none !important;
    background: white !important;
}}
[data-testid="stTextInput"] label {{
    color: #64748B !important; font-size: 0.72rem !important;
    font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {{
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important; color: #1E293B !important;
}}
[data-testid="stSelectbox"] > div > div > div {{
    color: #1E293B !important;
}}
[data-testid="stSelectbox"] label {{
    color: #64748B !important; font-size: 0.72rem !important;
    font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}

/* ── Primary button ── */
[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, {accent}, {accent_dark}) !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.7rem 1.5rem !important; font-weight: 600 !important;
    font-size: 0.95rem !important; color: white !important;
    box-shadow: 0 4px 18px {accent}35 !important;
    transition: all 0.18s !important; letter-spacing: 0.01em !important;
}}
[data-testid="stButton"] > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px {accent}45 !important;
}}
[data-testid="stButton"] > button[kind="primary"]:active {{ transform: translateY(0) !important; }}

/* ── Secondary button ── */
[data-testid="stButton"] > button[kind="secondary"] {{
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    color: #64748B !important; border-radius: 10px !important;
    transition: all 0.15s !important;
}}
[data-testid="stButton"] > button[kind="secondary"]:hover {{
    border-color: #CBD5E1 !important;
    color: #475569 !important;
    background: #F8FAFC !important;
}}

/* ── Tabs ── */
[data-baseweb="tab-list"] {{
    background: #F1F5F9 !important;
    border-radius: 12px !important; padding: 4px !important; gap: 2px !important;
    border: 1px solid #E2E8F0 !important; margin-bottom: 1rem !important;
}}
[data-baseweb="tab"] {{
    background: transparent !important; border-radius: 8px !important;
    color: #64748B !important; font-size: 0.82rem !important;
    font-weight: 500 !important; border: none !important;
    padding: 0.5rem 1.25rem !important; transition: all 0.15s !important;
}}
[data-baseweb="tab"]:hover {{ color: #334155 !important; background: rgba(255,255,255,0.8) !important; }}
[aria-selected="true"][data-baseweb="tab"] {{
    background: white !important;
    color: {accent} !important; font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}}
[data-baseweb="tab-border"],
[data-baseweb="tab-highlight"] {{ display: none !important; }}

/* ── Alerts ── */
[data-testid="stAlert"] {{ border-radius: 10px !important; font-size: 0.875rem !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: #CBD5E1; border-radius: 2px; }}
</style>"""


def auth_header(icon: str, title: str, subtitle: str = "",
                accent: str = "#2563EB") -> None:
    """Logo + titre centré pour les pages d'authentification (thème clair)."""
    sub = (f'<p style="color:#64748B;font-size:0.875rem;margin:0.5rem 0 0;line-height:1.5">'
           f'{subtitle}</p>') if subtitle else ""
    st.markdown(f"""
<div style="text-align:center;margin-bottom:2rem">
    <div style="width:74px;height:74px;
                background:linear-gradient(135deg,{accent},{accent}AA);
                border-radius:22px;margin:0 auto 1.25rem;
                display:flex;align-items:center;justify-content:center;
                font-size:2.3rem;
                box-shadow:0 8px 28px {accent}30;
                border:1px solid {accent}20">
        {icon}
    </div>
    <h1 style="color:#1E293B;font-family:'Poppins',sans-serif;
               font-size:1.75rem;font-weight:700;margin:0;line-height:1.2">
        {title}
    </h1>
    {sub}
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD HEADER — en-tête gradient réutilisable
# ══════════════════════════════════════════════════════════════════════════════

def dashboard_header(title: str, subtitle: str = "", icon: str = "",
                     color_a: str = "#2563EB", color_b: str = "#1D4ED8") -> None:
    icon_html = (f"<span style='font-size:1.4rem;margin-right:0.6rem'>{icon}</span>"
                 if icon else "")
    sub_html  = (f"<p style='margin:0.35rem 0 0;opacity:0.82;font-size:0.84rem;"
                 f"line-height:1.4;font-weight:400'>{subtitle}</p>") if subtitle else ""
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{color_a} 0%,{color_b} 100%);
            border-radius:16px;padding:1.25rem 1.75rem;color:white;
            margin-bottom:1.5rem;position:relative;overflow:hidden;
            box-shadow:0 6px 24px {color_a}44,0 2px 6px {color_a}22">
    <div style="position:absolute;top:-24px;right:-24px;width:130px;height:130px;
                border-radius:50%;background:rgba(255,255,255,0.07)"></div>
    <div style="position:absolute;bottom:-32px;right:80px;width:90px;height:90px;
                border-radius:50%;background:rgba(255,255,255,0.05)"></div>
    <h2 style="margin:0;font-family:'Poppins',sans-serif;font-size:1.3rem;
               font-weight:700;display:flex;align-items:center;position:relative;z-index:1">
        {icon_html}{title}
    </h2>
    <div style="position:relative;z-index:1">{sub_html}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    if icon:
        st.markdown(f"""
<div class="section-header">
    <span style="font-size:1.6rem">{icon}</span>
    <h2>{title}</h2>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-header"><h2>{title}</h2></div>',
                    unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def breadcrumb(*items) -> None:
    parts = []
    for i, item in enumerate(items):
        label = item[0] if isinstance(item, tuple) else item
        parts.append(
            f"<span style='color:#1E293B;font-weight:500'>{label}</span>"
            if i == len(items) - 1 else label
        )
    st.markdown(
        f'<div style="font-size:0.82rem;color:#94A3B8;margin-bottom:0.75rem">'
        f'🏠 {" &rsaquo; ".join(parts)}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# STAT CARD
# ══════════════════════════════════════════════════════════════════════════════

def stat_card(value, label: str, icon: str = "", col=None) -> None:
    icon_html = f'<div class="s-icon">{icon}</div>' if icon else ""
    html = (f'<div class="stat-card">{icon_html}'
            f'<div class="s-value">{value}</div>'
            f'<div class="s-label">{label}</div></div>')
    (col or st).markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSITY CARD
# ══════════════════════════════════════════════════════════════════════════════

def university_card(uni: dict) -> None:
    photo   = (uni.get("photo_url")
               or "https://images.unsplash.com/photo-1562774053-701939374585?w=400")
    address = uni.get("address") or "Adresse non renseignée"
    st.markdown(f"""
<div class="uni-card">
    <img src="{photo}" style="width:100%;height:130px;object-fit:cover;border-radius:8px"
         alt="{uni['name']}">
    <h3>{uni['name']}</h3>
    <p>📍 {address}</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENT CARD
# ══════════════════════════════════════════════════════════════════════════════

def announcement_card(ann: dict) -> None:
    from utils.storage import get_file_base64, get_file_bytes, is_image

    pinned_class = "pinned" if ann.get("is_pinned") else ""
    pinned_icon  = "📌 "   if ann.get("is_pinned") else ""
    date = ann.get("created_at")
    if isinstance(date, datetime):
        date_str = date.strftime("%d/%m/%Y")
    else:
        date_str = str(date)[:10] if date else ""

    file_url  = ann.get("file_url")
    file_name = ann.get("file_name") or ""
    file_badge = ""
    if file_url:
        if is_image(file_url):
            file_badge = " &middot; 🖼️ Image jointe"
        else:
            file_badge = " &middot; 📎 PDF joint"

    st.markdown(f"""
<div class="announcement {pinned_class}">
    <h4>{pinned_icon}{ann['title']}</h4>
    <p>{ann['content']}</p>
    <small style="color:#94A3B8;font-size:0.75rem">{date_str}{file_badge}</small>
</div>
""", unsafe_allow_html=True)

    if file_url:
        _ann_id  = ann.get("id", id(ann))
        _key_vis = f"file_ann_{_ann_id}"

        if is_image(file_url):
            # ── Affichage image ───────────────────────────────────────────────
            col_view, col_dl, _ = st.columns([1, 1, 3])
            with col_view:
                if st.button("👁️ Voir l'image", key=f"view_{_key_vis}"):
                    st.session_state[_key_vis] = not st.session_state.get(_key_vis, False)
            with col_dl:
                file_data = get_file_bytes(file_url)
                if file_data:
                    dl_name = file_name or file_url.split("/")[-1]
                    st.download_button(
                        "⬇️ Télécharger", data=file_data,
                        file_name=dl_name, key=f"dl_{_key_vis}"
                    )
            if st.session_state.get(_key_vis):
                data_uri = get_file_base64(file_url)
                if data_uri:
                    st.markdown(
                        f'<img src="{data_uri}" '
                        f'style="max-width:100%;border-radius:10px;'
                        f'margin-top:0.5rem;border:1px solid #E2E8F0">',
                        unsafe_allow_html=True,
                    )
        else:
            # ── Affichage PDF ─────────────────────────────────────────────────
            col_view, col_dl, _ = st.columns([1, 1, 3])
            with col_view:
                if st.button("👁️ Lire le PDF", key=f"view_{_key_vis}"):
                    st.session_state[_key_vis] = not st.session_state.get(_key_vis, False)
            with col_dl:
                file_data = get_file_bytes(file_url)
                if file_data:
                    dl_name = file_name or file_url.split("/")[-1]
                    st.download_button(
                        "⬇️ Télécharger", data=file_data,
                        file_name=dl_name, key=f"dl_{_key_vis}",
                        mime="application/pdf"
                    )
            if st.session_state.get(_key_vis):
                data_uri = get_file_base64(file_url)
                if data_uri:
                    st.markdown(
                        f'<iframe src="{data_uri}" width="100%" height="620px" '
                        f'style="border:1px solid #E2E8F0;border-radius:10px;'
                        f'margin-top:0.5rem"></iframe>',
                        unsafe_allow_html=True,
                    )


# ══════════════════════════════════════════════════════════════════════════════
# ROLE BADGE
# ══════════════════════════════════════════════════════════════════════════════

def role_badge(role: str) -> None:
    badge_map = {
        "super_admin":       ("Super Admin",  "badge-super"),
        "admin_universite":  ("Admin Univ.",  "badge-univ"),
        "admin_faculte":     ("Admin Fac.",   "badge-fac"),
        "admin_departement": ("Admin Dépt.",  "badge-dept"),
    }
    label, css = badge_map.get(role, (role, "badge-super"))
    st.markdown(f'<span class="badge {css}">{label}</span>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# WEEK NAV
# ══════════════════════════════════════════════════════════════════════════════

def week_nav(key: str) -> tuple:
    """Navigation semaine avec badges. Retourne (day_dates, week_type, week_num)."""
    from datetime import date as _date, timedelta as _td
    today = _date.today()
    # Le dimanche, l'école commence demain : afficher la semaine suivante par défaut
    if key not in st.session_state and today.weekday() == 6:
        st.session_state[key] = 1
    offset    = st.session_state.get(key, 0)
    monday    = today - _td(days=today.weekday()) + _td(weeks=offset)
    week_num  = monday.isocalendar()[1]
    week_type = "Paire" if week_num % 2 == 0 else "Impaire"
    wt_label  = "Semaine 2" if week_type == "Paire" else "Semaine 1"
    saturday  = monday + _td(days=5)
    DAYS      = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"]
    day_dates = {day: (monday + _td(days=i)).strftime("%d/%m")
                 for i, day in enumerate(DAYS)}

    pcolor = "#2563EB" if week_type == "Paire" else "#7C3AED"
    wt_badge = (f"<span style='background:{pcolor}18;color:{pcolor};"
                f"padding:0.15rem 0.55rem;border-radius:999px;"
                f"font-size:0.72rem;font-weight:600;letter-spacing:0.02em'>"
                f"{wt_label}</span>")

    col_prev, col_wk, col_next, col_rst = st.columns([1, 8, 1, 1])
    with col_prev:
        if st.button("◀", key=f"{key}_prev", help="Semaine précédente"):
            st.session_state[key] = offset - 1; st.rerun()
    with col_wk:
        st.markdown(
            f"<div style='text-align:center;padding:0.35rem 0'>"
            f"<span style='font-family:Poppins,sans-serif;font-weight:800;"
            f"color:#1E293B;font-size:1rem;letter-spacing:-0.01em'>Sem. {week_num}</span>"
            f"<span style='color:#E2E8F0;margin:0 0.6rem;font-size:0.9rem'>│</span>"
            f"<span style='color:#475569;font-size:0.82rem'>"
            f"{monday.strftime('%d %b')} – {saturday.strftime('%d %b %Y')}</span>"
            f"<span style='margin-left:0.6rem'>{wt_badge}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("▶", key=f"{key}_next", help="Semaine suivante"):
            st.session_state[key] = offset + 1; st.rerun()
    with col_rst:
        if offset != 0 and st.button("↺", key=f"{key}_reset",
                                      help="Retour à la semaine actuelle"):
            st.session_state[key] = 0; st.rerun()

    return day_dates, week_type, week_num, monday


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULE TABLE — implémentation unifiée
# ══════════════════════════════════════════════════════════════════════════════

def _initials(name: str) -> str:
    parts = (name or "").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"


def render_schedule_table(schedules: list, day_dates: dict = None) -> None:
    if not schedules:
        empty_state("Aucun cours planifié pour cette semaine.", "📅")
        return

    DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

    time_slots = sorted(set(
        (fmt_time(s["start_time"]), fmt_time(s["end_time"]))
        for s in schedules
    ))

    grid = {slot: {day: [] for day in DAYS} for slot in time_slots}
    for s in schedules:
        slot = (fmt_time(s["start_time"]), fmt_time(s["end_time"]))
        if s["day"] in DAYS and slot in grid:
            grid[slot][s["day"]].append(s)

    html = '<div class="sched-wrap"><table class="sched"><thead><tr>'
    html += '<th class="time-th">⏱ Heure</th>'
    for day in DAYS:
        date_lbl = (f"<span class='day-date'>{day_dates[day]}</span>"
                    if day_dates else "")
        html += f"<th>{day}{date_lbl}</th>"
    html += "</tr></thead><tbody>"

    for (start, end) in time_slots:
        html += (f'<tr><td class="time-td">'
                 f'<span style="color:#1E293B;font-size:0.80rem">{start}</span>'
                 f'<br><span style="color:#CBD5E1;font-size:0.58rem">▼</span>'
                 f'<br><span style="color:#1E293B;font-size:0.80rem">{end}</span>'
                 f'</td>')
        for day in DAYS:
            cells = grid[(start, end)][day]
            if cells:
                html += "<td>"
                for s in cells:
                    stype     = s.get("slot_type") or "cours"
                    room      = s.get("room") or "—"
                    status    = s.get("slot_status") or "actif"
                    sub       = s.get("substitute_name")
                    prof_disp = sub or s.get("professor_name", "")
                    _opacity  = "0.42" if status == "annule" else "1"
                    _extra    = f"opacity:{_opacity};"
                    _av_init  = _initials(prof_disp)
                    if stype == "ferie":
                        html += (
                            f'<div class="slot slot-ferie" style="{_extra}">'
                            f'<div class="sn sn-ferie">🚫 {s["course_name"]}</div>'
                            f'<span class="slot-type-badge badge-ferie">Férié</span>'
                            f'</div>'
                        )
                    elif stype == "examen":
                        _av = (f'<span class="prof-av prof-av-examen">{_av_init}</span>'
                               if prof_disp else "")
                        html += (
                            f'<div class="slot slot-examen" style="{_extra}">'
                            f'<div class="sn sn-examen">📝 {s["course_name"]}</div>'
                            f'<div class="sp sp-examen">{_av}{prof_disp}</div>'
                            f'<div class="sr sr-examen">🏛 {room}</div>'
                            f'<span class="slot-type-badge badge-examen">Examen</span>'
                            f'</div>'
                        )
                    else:
                        _status_badge = ""
                        if status == "annule":
                            _status_badge = '<span class="slot-type-badge" style="background:#FEE2E2;color:#991B1B">ANNULÉ</span>'
                        elif status == "remplace":
                            _status_badge = '<span class="slot-type-badge" style="background:#FEF3C7;color:#92400E">REMPLACÉ</span>'
                        _sub_pfx = "🔄 " if sub else ""
                        _av = (f'<span class="prof-av prof-av-cours">{_av_init}</span>'
                               if prof_disp else "")
                        html += (
                            f'<div class="slot slot-cours" style="{_extra}">'
                            f'<div class="sn sn-cours">{s["course_name"]}</div>'
                            f'<div class="sp sp-cours">{_av}{_sub_pfx}{prof_disp}</div>'
                            f'<div class="sr sr-cours">📍 {room}</div>'
                            f'{_status_badge}'
                            f'</div>'
                        )
                html += "</td>"
            else:
                html += '<td style="background:rgba(248,250,255,0.6)"></td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# EMPTY STATE
# ══════════════════════════════════════════════════════════════════════════════

def empty_state(message: str, icon: str = "📭", sub: str = "") -> None:
    sub_html = f'<p class="es-sub">{sub}</p>' if sub else ""
    st.markdown(f"""
<div class="empty-state">
    <div class="es-icon">{icon}</div>
    <p class="es-text">{message}</p>
    {sub_html}
</div>
""", unsafe_allow_html=True)
