# utils/chatbot.py — Chatbot IA UniBot basé sur Claude (Anthropic)
import streamlit as st
import anthropic
from datetime import datetime


def _get_client() -> anthropic.Anthropic:
    try:
        key = st.secrets["anthropic"]["api_key"]
    except Exception:
        raise ValueError(
            "Clé API Anthropic manquante. Ajoutez [anthropic] api_key = '...' "
            "dans .streamlit/secrets.toml"
        )
    return anthropic.Anthropic(api_key=key)


# ── Prompts système par profil ────────────────────────────────────────────────

_BASE_PROMPT = """Tu es UniBot, l'assistant intelligent de UniSchedule.
UniSchedule est une plateforme de gestion universitaire qui permet de gérer
les emplois du temps, les notes, les réclamations, les bulletins et les communications.

Règles importantes :
- Tu réponds TOUJOURS en français, avec un ton sympathique et accessible.
- Tu es concis : maximum 3-4 phrases par réponse sauf si on te demande plus de détails.
- Tu n'inventes jamais de données — tu utilises uniquement les informations fournies.
- Si tu ne sais pas quelque chose, tu le dis honnêtement.
- Tu peux utiliser des emojis avec modération pour rendre les réponses plus agréables.
- Date du jour : {today}
"""

def _system_student(student: dict, grades: list, schedule: list,
                     claims: list, results: list) -> str:
    grades_txt = ""
    if grades:
        by_course = {}
        for g in grades:
            by_course.setdefault(g.get("course_name", "?"), []).append(g)
        for course, gs in by_course.items():
            grades_txt += f"\n  {course} :"
            for g in gs:
                grades_txt += (
                    f"\n    - {g.get('exam_type','?')} : "
                    f"{g.get('grade','?')}/{g.get('max_grade','?')} "
                    f"(session {g.get('session_name','?')})"
                )
    else:
        grades_txt = "\n  Aucune note publiée pour l'instant."

    schedule_txt = ""
    if schedule:
        upcoming = schedule[:5]
        for s in upcoming:
            schedule_txt += (
                f"\n  - {s.get('course_name','?')} | "
                f"{s.get('day_of_week','?')} "
                f"{str(s.get('start_time','?'))[:5]}–{str(s.get('end_time','?'))[:5]} | "
                f"Salle {s.get('room_name','?')}"
            )
    else:
        schedule_txt = "\n  Aucun cours dans l'emploi du temps."

    claims_txt = ""
    if claims:
        for c in claims:
            claims_txt += (
                f"\n  - {c.get('course_name','?')} ({c.get('exam_type','?')}) : "
                f"statut = {c.get('status','?')}"
            )
    else:
        claims_txt = "\n  Aucune réclamation en cours."

    results_txt = ""
    if results:
        for r in results:
            results_txt += (
                f"\n  - Session {r.get('session_name','?')} : "
                f"moyenne {r.get('average','?')}/20 | "
                f"rang {r.get('rank','?')} | "
                f"décision : {r.get('decision','?')}"
            )
    else:
        results_txt = "\n  Aucune décision calculée."

    avg = ""
    if grades:
        vals = [g["grade"] / g["max_grade"] * 20
                for g in grades if g.get("max_grade")]
        if vals:
            avg = f"{sum(vals)/len(vals):.2f}/20"

    return _BASE_PROMPT.format(today=datetime.now().strftime("%d/%m/%Y")) + f"""
Tu parles avec un ÉTUDIANT. Voici ses informations :

Identité :
  Nom complet    : {student.get('full_name', '?')}
  Numéro étudiant: {student.get('student_number', '?')}
  Classe         : {student.get('class_name', student.get('class_id', '?'))}
  Promotion      : {student.get('promotion_name', '?')}
  Moyenne générale actuelle : {avg or 'non calculée'}

Ses notes publiées :{grades_txt}

Ses prochains cours :{schedule_txt}

Ses réclamations :{claims_txt}

Ses résultats de session :{results_txt}

Tu peux l'aider à :
- Comprendre ses notes et sa moyenne
- Savoir comment contester une note
- Comprendre son emploi du temps
- Savoir comment soumettre un TP
- Comprendre le processus de réclamation
- Lire son bulletin
- Utiliser l'application en général
"""


def _system_professor(prof: dict, classes: list, pending_claims: list) -> str:
    classes_txt = ""
    if classes:
        for c in classes:
            classes_txt += f"\n  - {c.get('name','?')} ({c.get('promotion_name','')})"
    else:
        classes_txt = "\n  Aucune classe assignée."

    claims_txt = ""
    if pending_claims:
        claims_txt = f"\n  {len(pending_claims)} réclamation(s) en attente de réponse."
    else:
        claims_txt = "\n  Aucune réclamation en attente."

    return _BASE_PROMPT.format(today=datetime.now().strftime("%d/%m/%Y")) + f"""
Tu parles avec un PROFESSEUR. Voici ses informations :

Identité :
  Nom : {prof.get('name', prof.get('full_name', '?'))}

Ses classes :{classes_txt}

Réclamations :{claims_txt}

Tu peux l'aider à :
- Comprendre comment saisir et soumettre des notes
- Répondre aux réclamations étudiantes
- Gérer les TPs et documents de cours
- Utiliser l'application en général
"""


def _system_admin(user: dict, dept_name: str = "") -> str:
    return _BASE_PROMPT.format(today=datetime.now().strftime("%d/%m/%Y")) + f"""
Tu parles avec un ADMINISTRATEUR. Voici ses informations :

Identité :
  Nom        : {user.get('name', '?')}
  Rôle       : {user.get('role', '?')}
  Département: {dept_name or '?'}

Tu peux l'aider à :
- Gérer la structure de l'université (facultés, départements, promotions, classes)
- Valider et publier les notes
- Gérer les réclamations et les bulletins
- Créer des comptes (admins, profs, étudiants)
- Utiliser l'application en général
"""


# ── Interface Streamlit ───────────────────────────────────────────────────────

def render_chatbot(system_prompt: str, session_key: str = "chatbot_messages"):
    """
    Affiche l'interface chatbot.
    system_prompt : le prompt système adapté au profil de l'utilisateur.
    session_key   : clé unique dans st.session_state pour les messages.
    """
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    messages: list = st.session_state[session_key]

    # ── Affichage des messages ────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not messages:
            st.markdown(
                "<div style='text-align:center;padding:2rem;color:#94A3B8'>"
                "🤖 <b>UniBot</b><br>"
                "Bonjour ! Je suis ton assistant UniSchedule.<br>"
                "Pose-moi n'importe quelle question sur l'application ou tes données."
                "</div>",
                unsafe_allow_html=True,
            )
        for msg in messages:
            role  = msg["role"]
            content = msg["content"]
            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)

    # ── Saisie utilisateur ────────────────────────────────────────────────────
    user_input = st.chat_input("Pose ta question à UniBot…")

    if user_input:
        messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("UniBot réfléchit…"):
                try:
                    client = _get_client()
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1024,
                        system=system_prompt,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in messages
                        ],
                    )
                    reply = response.content[0].text
                except ValueError as ve:
                    reply = f"⚠️ {ve}"
                except Exception as e:
                    reply = f"❌ Erreur UniBot : {e}"

            st.markdown(reply)

        messages.append({"role": "assistant", "content": reply})
        st.session_state[session_key] = messages

    # ── Bouton vider ─────────────────────────────────────────────────────────
    if messages:
        if st.button("🗑️ Vider la conversation", key=f"clear_{session_key}"):
            st.session_state[session_key] = []
            st.rerun()
