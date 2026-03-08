# pages/1_Accueil.py — Page d'accueil étudiant
import streamlit as st
from db.queries import UniversityQueries
from utils.components import inject_global_css

inject_global_css()

st.markdown("""
<style>
    /* Bannière hero */
    .hero {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #0EA5E9 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero h1 { margin:0; font-family:'Poppins',sans-serif; font-size:2.2rem; font-weight:700; }
    .hero p  { margin:0.4rem 0 0; opacity:0.88; font-size:1rem; }

    /* Carte université */
    .uni-card {
        background: white;
        border: 2px solid #E2E8F0;
        border-radius: 14px;
        overflow: hidden;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .uni-card:hover {
        border-color: #2563EB;
        box-shadow: 0 6px 24px rgba(37,99,235,0.15);
        transform: translateY(-3px);
    }
    .uni-card img { width:100%; height:130px; object-fit:cover; }
    .uni-card-body { padding: 0.9rem 1rem; }
    .uni-card-body h4 { margin:0 0 0.25rem; color:#1E293B; font-size:0.95rem; font-weight:600; }
    .uni-card-body p  { margin:0; color:#64748B; font-size:0.78rem; }

    /* Carte pub */
    .pub-card {
        background: linear-gradient(135deg, #F8FAFC, #EFF6FF);
        border: 1px dashed #CBD5E1;
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎓 UniSchedule</h1>
    <p>Consultez votre emploi du temps en quelques secondes — sans inscription</p>
</div>
""", unsafe_allow_html=True)

# ── Layout : Universités (gauche) + Pub (droite) ──────────────────────────────
col_unis, col_pub = st.columns([3, 1], gap="large")

with col_unis:
    st.markdown("#### 🏛️ Choisissez votre université")
    search = st.text_input("", placeholder="🔍  Rechercher une université...", label_visibility="collapsed")

    try:
        universities = UniversityQueries.get_all()
    except Exception as e:
        st.error(f"❌ Connexion impossible : {e}")
        st.info("💡 Configurez `.streamlit/secrets.toml`")
        st.stop()

    if search:
        universities = [u for u in universities
                        if search.lower() in u["name"].lower()
                        or (u.get("address") and search.lower() in u["address"].lower())]

    if not universities:
        st.info("Aucune université trouvée.")
    else:
        # Grille 3 colonnes
        cols = st.columns(3, gap="medium")
        for i, uni in enumerate(universities):
            with cols[i % 3]:
                photo = uni.get("photo_url") or "https://images.unsplash.com/photo-1562774053-701939374585?w=400"
                address = uni.get("address") or "—"
                st.markdown(f"""
                <div class="uni-card">
                    <img src="{photo}" alt="{uni['name']}">
                    <div class="uni-card-body">
                        <h4>{uni['name']}</h4>
                        <p>📍 {address}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Voir l'horaire →", key=f"uni_{uni['id']}", use_container_width=True, type="primary"):
                    st.session_state["sel_uni_id"]   = uni["id"]
                    st.session_state["sel_uni_name"] = uni["name"]
                    st.switch_page("pages/2_Horaire.py")

    st.caption(f"{len(universities)} université(s) disponible(s)")

with col_pub:
    st.markdown("#### 📢 Partenaires")
    st.markdown("""
    <div class="pub-card">
        <div style="font-size:2.5rem">📣</div>
        <div style="color:#94A3B8;font-size:0.8rem;font-weight:500">ESPACE PUBLICITAIRE</div>
        <div style="color:#CBD5E1;font-size:0.72rem">
            Contactez-nous pour afficher<br>votre publicité ici
        </div>
        <a href="mailto:contact@unischedule.dz"
           style="background:#2563EB;color:white;padding:0.4rem 1rem;border-radius:8px;
                  text-decoration:none;font-size:0.78rem;font-weight:600">
            Nous contacter
        </a>
    </div>
    <br>
    <div class="pub-card" style="margin-top:0">
        <div style="font-size:2rem">🤝</div>
        <div style="color:#94A3B8;font-size:0.8rem;font-weight:500">PARTENARIAT</div>
        <div style="color:#CBD5E1;font-size:0.72rem">
            Votre bannière<br>partenaire ici
        </div>
    </div>
    """, unsafe_allow_html=True)
