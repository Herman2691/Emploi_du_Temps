import streamlit as st

st.set_page_config(
    page_title="UniSchedule",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.components import inject_global_css
from utils.auth import get_current_user, logout

inject_global_css()
user = get_current_user()

public_pages = [
    st.Page("pages/1_Accueil.py",  title="Accueil",         icon="🏠", default=True),
    st.Page("pages/2_Horaire.py",  title="Mon Horaire",     icon="📅"),
]

admin_pages = [
    st.Page("pages/7_Admin_Login.py",     title="Connexion Admin", icon="🔑"),
    st.Page("pages/8_Admin_Dashboard.py", title="Dashboard Admin", icon="📊"),
]

if user:
    all_pages = {
        "🌐 Espace Étudiant": public_pages,
        "⚙️ Administration":  admin_pages,
    }
else:
    all_pages = {
        "🌐 Espace Étudiant": public_pages,
        "ADMIN": admin_pages,
    }
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] a[href*="Admin"],
        section[data-testid="stSidebar"] a[href*="Dashboard"] { display:none!important; }
        section[data-testid="stSidebar"] nav ul li:last-child { display:none!important; }
    </style>
    <script>
    function hideAdmin() {
        document.querySelectorAll('section[data-testid="stSidebar"] a').forEach(function(a){
            if(a.href && (a.href.includes('Admin') || a.href.includes('Dashboard'))){
                var li = a.closest('li'); if(li) li.style.display='none';
            }
        });
        document.querySelectorAll('section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span').forEach(function(el){
            if(el.textContent.trim()==='ADMIN'){ var p=el.closest('li')||el.parentElement; if(p) p.style.display='none'; }
        });
    }
    hideAdmin();
    new MutationObserver(hideAdmin).observe(document.body,{childList:true,subtree:true});
    </script>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 0.25rem">
        <h2 style="margin:0;font-family:'Poppins',sans-serif;color:#1E293B;font-size:1.4rem">🎓 UniSchedule</h2>
        <p style="margin:0;color:#64748B;font-size:0.78rem">Emplois du temps universitaires</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    if user:
        role_labels = {
            "super_admin":("🔴","Super Admin"),
            "admin_universite":("🔵","Admin Université"),
            "admin_faculte":("🟢","Admin Faculté"),
            "admin_departement":("🟡","Admin Département"),
        }
        icon_r, label_r = role_labels.get(user["role"],("⚪",user["role"]))
        st.markdown(f"""
        <div style="background:#F1F5F9;border-radius:8px;padding:0.6rem 0.8rem;margin-bottom:0.75rem">
            <div style="font-weight:600;color:#1E293B;font-size:0.9rem">👤 {user['name']}</div>
            <div style="color:#64748B;font-size:0.78rem">{icon_r} {label_r}</div>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Se déconnecter", use_container_width=True, type="secondary"):
            logout(); st.rerun()
        st.divider()
    st.caption("© 2025 UniSchedule v1.0")

pg = st.navigation(all_pages)
pg.run()
