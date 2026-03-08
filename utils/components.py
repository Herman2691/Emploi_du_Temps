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


def inject_global_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        :root {
            --primary: #2563EB; --primary-dark: #1D4ED8;
            --success: #10B981; --warning: #F59E0B;
            --danger: #EF4444;  --accent: #06B6D4;
            --border: #E2E8F0;  --text-muted: #64748B;
        }
        #MainMenu, footer { visibility: hidden; }

        .uni-card {
            background: white; border: 1px solid var(--border);
            border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;
            transition: all 0.2s ease;
        }
        .uni-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 20px rgba(37,99,235,0.12);
            transform: translateY(-2px);
        }
        .uni-card h3 { color:#1E293B; margin:0.5rem 0 0.25rem; font-family:'Poppins',sans-serif; }
        .uni-card p  { color:var(--text-muted); font-size:0.875rem; margin:0; }

        .badge { display:inline-block; padding:0.2rem 0.7rem; border-radius:20px; font-size:0.75rem; font-weight:600; }
        .badge-super { background:#FEF3C7; color:#92400E; }
        .badge-univ  { background:#DBEAFE; color:#1E40AF; }
        .badge-fac   { background:#D1FAE5; color:#065F46; }
        .badge-dept  { background:#EDE9FE; color:#4C1D95; }

        .announcement { border-left:4px solid var(--primary); background:#EFF6FF; padding:0.75rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.75rem; }
        .announcement.pinned { border-left-color:var(--warning); background:#FFFBEB; }
        .announcement h4 { margin:0 0 0.25rem; color:#1E293B; font-size:0.95rem; }
        .announcement p  { margin:0; color:var(--text-muted); font-size:0.85rem; }

        .section-header { display:flex; align-items:center; gap:0.5rem; border-bottom:2px solid var(--border); padding-bottom:0.5rem; margin-bottom:1rem; }
        .section-header h2 { margin:0; font-family:'Poppins',sans-serif; color:#1E293B; font-size:1.4rem; }

        .stat-card { background:white; border:1px solid var(--border); border-radius:10px; padding:1rem 1.25rem; text-align:center; }
        .stat-card .value { font-size:2rem; font-weight:700; font-family:'Poppins',sans-serif; color:var(--primary); }
        .stat-card .label { color:var(--text-muted); font-size:0.8rem; margin-top:0.2rem; }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """En-tête standardisé — N'appelle PAS inject_global_css (évite double injection)."""
    if icon:
        st.markdown(f"""
        <div class="section-header">
            <span style="font-size:1.8rem">{icon}</span>
            <h2>{title}</h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-header"><h2>{title}</h2></div>',
                    unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def breadcrumb(*items):
    parts = []
    for i, item in enumerate(items):
        label = item[0] if isinstance(item, tuple) else item
        parts.append(f"<span>{label}</span>" if i == len(items)-1 else label)
    st.markdown(f'<div style="font-size:0.85rem;color:#64748B;margin-bottom:1rem">🏠 {" › ".join(parts)}</div>',
                unsafe_allow_html=True)


def stat_card(value, label: str, col=None):
    html = f'<div class="stat-card"><div class="value">{value}</div><div class="label">{label}</div></div>'
    (col or st).markdown(html, unsafe_allow_html=True)


def university_card(uni: dict):
    photo   = uni.get("photo_url") or "https://images.unsplash.com/photo-1562774053-701939374585?w=400"
    address = uni.get("address") or "Adresse non renseignée"
    st.markdown(f"""
    <div class="uni-card">
        <img src="{photo}" style="width:100%;height:140px;object-fit:cover;border-radius:8px">
        <h3>{uni['name']}</h3>
        <p>📍 {address}</p>
    </div>
    """, unsafe_allow_html=True)


def announcement_card(ann: dict):
    pinned_class = "pinned" if ann.get("is_pinned") else ""
    pinned_icon  = "📌 "   if ann.get("is_pinned") else ""
    date = ann.get("created_at")
    if isinstance(date, datetime):
        date_str = date.strftime("%d/%m/%Y")
    else:
        date_str = str(date)[:10] if date else ""
    st.markdown(f"""
    <div class="announcement {pinned_class}">
        <h4>{pinned_icon}{ann['title']}</h4>
        <p>{ann['content']}</p>
        <small style="color:#94A3B8">{date_str}</small>
    </div>
    """, unsafe_allow_html=True)


def role_badge(role: str):
    badge_map = {
        "super_admin":       ("Super Admin",  "badge-super"),
        "admin_universite":  ("Admin Univ.",  "badge-univ"),
        "admin_faculte":     ("Admin Fac.",   "badge-fac"),
        "admin_departement": ("Admin Dépt.",  "badge-dept"),
    }
    label, css = badge_map.get(role, (role, "badge-super"))
    st.markdown(f'<span class="badge {css}">{label}</span>', unsafe_allow_html=True)


def render_schedule_table(schedules: list):
    """Grille hebdomadaire pour le dashboard admin — utilise fmt_time()."""
    if not schedules:
        st.info("📭 Aucun cours planifié.")
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

    html = """
    <style>
        .sched-table { width:100%; border-collapse:collapse; font-size:0.8rem; }
        .sched-table th { background:#2563EB; color:white; padding:8px 12px; text-align:center; border:1px solid #1D4ED8; }
        .sched-table td { border:1px solid #E2E8F0; padding:4px; vertical-align:top; min-width:100px; height:60px; }
        .sched-table .time-col { background:#F1F5F9; font-weight:600; color:#475569; text-align:center; font-size:0.75rem; width:110px; vertical-align:middle; }
        .cell-course { background:#EFF6FF; border-left:3px solid #2563EB; border-radius:4px; padding:4px 6px; margin:2px; }
        .cell-course .cn { font-weight:600; color:#1E40AF; font-size:0.78rem; }
        .cell-course .cp { color:#64748B; font-size:0.72rem; }
        .cell-course .cr { color:#06B6D4; font-size:0.7rem; }
    </style>
    <div style="overflow-x:auto"><table class="sched-table"><thead><tr><th>Horaire</th>"""
    for day in DAYS:
        html += f"<th>{day}</th>"
    html += "</tr></thead><tbody>"

    for (start, end) in time_slots:
        html += f"<tr><td class='time-col'>{start}<br>↓<br>{end}</td>"
        for day in DAYS:
            html += "<td>"
            for s in grid[(start, end)][day]:
                room = s.get("room") or "—"
                html += f"""<div class="cell-course">
                    <div class="cn">{s['course_name']}</div>
                    <div class="cp">👨‍🏫 {s['professor_name']}</div>
                    <div class="cr">📍 {room}</div>
                </div>"""
            html += "</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📭"):
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;color:#94A3B8">
        <div style="font-size:3rem">{icon}</div>
        <p style="margin-top:0.5rem">{message}</p>
    </div>
    """, unsafe_allow_html=True)
