# utils/chatbot.py — Chatbot IA UniBot basé sur Mistral AI
import streamlit as st
import streamlit.components.v1 as _components
import requests
import json
from datetime import datetime

_MISTRAL_URL   = "https://api.mistral.ai/v1/chat/completions"
_MISTRAL_MODEL = "open-mistral-7b"


_MISTRAL_KEY = "tTWI1SmLPtS2IhMuPJJfj3PvTvfYXUUZ"


def _get_api_key() -> str:
    try:
        return st.secrets["mistral"]["api_key"]
    except Exception:
        pass
    try:
        return st.secrets.mistral.api_key
    except Exception:
        pass
    return _MISTRAL_KEY


def _call_mistral(system_prompt: str, messages: list) -> str:
    """Appelle l'API Mistral et retourne la réponse texte."""
    api_key = _get_api_key()
    payload = {
        "model": _MISTRAL_MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    resp = requests.post(
        _MISTRAL_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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
        for s in schedule[:5]:
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

    vals = [g["grade"] / g["max_grade"] * 20
            for g in grades if g.get("max_grade")]
    avg = f"{sum(vals)/len(vals):.2f}/20" if vals else "non calculée"

    return _BASE_PROMPT.format(today=datetime.now().strftime("%d/%m/%Y")) + f"""
Tu parles avec un ÉTUDIANT. Voici ses informations :

Identité :
  Nom complet     : {student.get('full_name', '?')}
  Numéro étudiant : {student.get('student_number', '?')}
  Classe          : {student.get('class_name', student.get('class_id', '?'))}
  Promotion       : {student.get('promotion_name', '?')}
  Moyenne générale: {avg}

Ses notes publiées :{grades_txt}

Ses prochains cours :{schedule_txt}

Ses réclamations :{claims_txt}

Ses résultats de session :{results_txt}

Tu peux l'aider à :
- Comprendre ses notes et sa moyenne
- Savoir comment contester une note (réclamation)
- Comprendre son emploi du temps
- Savoir comment soumettre un TP
- Lire son bulletin
- Utiliser l'application en général
"""


def _system_professor(prof: dict, classes: list, pending_claims: list) -> str:
    classes_txt = "".join(
        f"\n  - {c.get('name','?')} ({c.get('promotion_name','')})"
        for c in classes
    ) or "\n  Aucune classe assignée."

    claims_txt = (
        f"\n  {len(pending_claims)} réclamation(s) en attente de réponse."
        if pending_claims else
        "\n  Aucune réclamation en attente."
    )

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
    """Affiche l'interface chatbot UniBot."""
    # Décale le chat input vers la gauche pour éviter le bouton "Manage App"
    st.markdown(
        """
        <style>
        div[data-testid="stChatInput"] {
            padding-right: 3.5rem !important;
        }
        div[data-testid="stChatInput"] > div {
            padding-right: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if session_key not in st.session_state:
        st.session_state[session_key] = []

    messages: list = st.session_state[session_key]

    # ── Historique ────────────────────────────────────────────────────────────
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
        with st.chat_message("user" if msg["role"] == "user" else "assistant",
                             avatar=None if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # ── Saisie ────────────────────────────────────────────────────────────────
    user_input = st.chat_input("Pose ta question à UniBot…")

    if user_input:
        messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("UniBot réfléchit…"):
                try:
                    reply = _call_mistral(system_prompt, messages)
                except ValueError as ve:
                    reply = f"⚠️ {ve}"
                except requests.HTTPError as he:
                    reply = f"❌ Erreur API Mistral ({he.response.status_code}) : {he.response.text[:200]}"
                except Exception as e:
                    reply = f"❌ Erreur UniBot : {e}"
            st.markdown(reply)

        messages.append({"role": "assistant", "content": reply})
        st.session_state[session_key] = messages

    # ── Vider ─────────────────────────────────────────────────────────────────
    if messages:
        if st.button("🗑️ Vider la conversation", key=f"clear_{session_key}"):
            st.session_state[session_key] = []
            st.rerun()


# ── Bulle flottante ───────────────────────────────────────────────────────────

def render_floating_chatbot(system_prompt: str, session_key: str = "chatbot_float"):
    """Bulle de chat flottante — injectée dans la page parente via components.v1.html."""
    api_key = _get_api_key()
    sk = session_key.replace("-", "_")

    # On utilise un template string (pas f-string) pour éviter les conflits avec {}
    _TMPL = """<script>
(function() {
  var pdoc = window.parent.document;
  var SK   = __SK__;
  var KEY  = __KEY__;
  var SYS  = __SYS__;
  var LS   = 'unibot_' + SK;
  var msgs = [];

  // Évite la double injection lors des reruns Streamlit
  if (pdoc.getElementById('ub-btn-' + SK)) return;

  // ── CSS ────────────────────────────────────────────────────────────────────
  var css = pdoc.createElement('style');
  css.textContent =
    '#ub-btn-'+SK+'{position:fixed;bottom:80px;right:24px;width:58px;height:58px;border-radius:50%;background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;font-size:26px;border:none;cursor:pointer;z-index:2147483647;box-shadow:0 4px 20px rgba(79,70,229,.55);display:flex;align-items:center;justify-content:center;transition:transform .2s}' +
    '#ub-btn-'+SK+':hover{transform:scale(1.1)}' +
    '#ub-panel-'+SK+'{position:fixed;bottom:150px;right:24px;width:350px;height:510px;background:#fff;border-radius:20px;box-shadow:0 16px 48px rgba(0,0,0,.22);display:none;flex-direction:column;z-index:2147483646;overflow:hidden;border:1px solid #E2E8F0}' +
    '#ub-head-'+SK+'{background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;padding:12px 14px;display:flex;align-items:center;gap:10px;flex-shrink:0}' +
    '#ub-msgs-'+SK+'{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:7px;background:#F8FAFC}' +
    '.ub-msg-'+SK+'{padding:9px 13px;border-radius:14px;max-width:84%;font-size:13px;line-height:1.5;word-wrap:break-word}' +
    '.ub-user-'+SK+'{background:#4F46E5;color:#fff;align-self:flex-end;border-bottom-right-radius:3px}' +
    '.ub-bot-'+SK+'{background:#fff;color:#1E293B;align-self:flex-start;border-bottom-left-radius:3px;box-shadow:0 1px 4px rgba(0,0,0,.08)}' +
    '#ub-typing-'+SK+'{color:#94A3B8;font-size:12px;padding:3px 10px;background:#F8FAFC;flex-shrink:0;display:none}' +
    '#ub-foot-'+SK+'{display:flex;gap:7px;padding:9px 11px;border-top:1px solid #E2E8F0;background:#fff;flex-shrink:0;align-items:center}' +
    '#ub-inp-'+SK+'{flex:1;border:1px solid #CBD5E1;border-radius:20px;padding:7px 13px;font-size:13px;outline:none;font-family:inherit}' +
    '#ub-inp-'+SK+':focus{border-color:#4F46E5;box-shadow:0 0 0 2px rgba(79,70,229,.15)}' +
    '#ub-send-'+SK+'{background:#4F46E5;color:#fff;border:none;border-radius:50%;width:34px;height:34px;cursor:pointer;font-size:15px;flex-shrink:0}' +
    '#ub-send-'+SK+':hover{background:#4338CA}' +
    '#ub-send-'+SK+':disabled{background:#94A3B8;cursor:default}';
  pdoc.head.appendChild(css);

  // ── HTML ───────────────────────────────────────────────────────────────────
  var root = pdoc.createElement('div');
  root.id = 'ub-root-' + SK;
  root.innerHTML =
    '<button id="ub-btn-'+SK+'">&#129302;</button>' +
    '<div id="ub-panel-'+SK+'">' +
      '<div id="ub-head-'+SK+'">' +
        '<span style="font-size:21px">&#129302;</span>' +
        '<div><div style="font-weight:600;font-size:14px">UniBot</div>' +
        '<div style="font-size:11px;opacity:.8">Assistant UniSchedule</div></div>' +
        '<button id="ub-close-'+SK+'" style="margin-left:auto;background:none;border:none;color:#fff;font-size:22px;cursor:pointer;line-height:1;padding:0">&times;</button>' +
      '</div>' +
      '<div id="ub-msgs-'+SK+'"></div>' +
      '<div id="ub-typing-'+SK+'">⏳ UniBot r\xe9fl\xe9chit…</div>' +
      '<div id="ub-foot-'+SK+'">' +
        '<input id="ub-inp-'+SK+'" placeholder="Pose ta question…">' +
        '<button id="ub-send-'+SK+'">➤</button>' +
      '</div>' +
    '</div>';
  pdoc.body.appendChild(root);

  // ── Logique ────────────────────────────────────────────────────────────────
  function g(id) { return pdoc.getElementById(id + '-' + SK); }

  function addMsg(role, text) {
    var d = pdoc.createElement('div');
    d.className = 'ub-msg-' + SK + ' ' + (role === 'user' ? 'ub-user-' : 'ub-bot-') + SK;
    d.textContent = text;
    var c = g('ub-msgs');
    c.appendChild(d);
    c.scrollTop = c.scrollHeight;
  }

  function save() { try { localStorage.setItem(LS, JSON.stringify(msgs)); } catch(e) {} }

  function restore() {
    try {
      var s = JSON.parse(localStorage.getItem(LS) || '[]');
      msgs = s;
      s.forEach(function(m) { addMsg(m.role, m.content); });
    } catch(e) {}
  }

  function toggle() {
    var p = g('ub-panel');
    var isOpen = p.style.display === 'flex';
    p.style.display = isOpen ? 'none' : 'flex';
    if (!isOpen) g('ub-inp').focus();
  }

  async function send() {
    var inp = g('ub-inp');
    var text = inp.value.trim();
    if (!text) return;
    inp.value = '';
    msgs.push({ role: 'user', content: text });
    addMsg('user', text);
    save();
    g('ub-typing').style.display = 'block';
    g('ub-send').disabled = true;
    try {
      var r = await fetch('https://api.mistral.ai/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'open-mistral-7b',
          max_tokens: 1024,
          messages: [{ role: 'system', content: SYS }].concat(msgs)
        })
      });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      var data = await r.json();
      var rep = (data.choices && data.choices[0]) ? data.choices[0].message.content : '❌ R\xe9ponse vide';
      msgs.push({ role: 'assistant', content: rep });
      addMsg('bot', rep);
      save();
    } catch(e) {
      addMsg('bot', '❌ Erreur : ' + e.message);
    }
    g('ub-typing').style.display = 'none';
    g('ub-send').disabled = false;
    g('ub-inp').focus();
  }

  g('ub-btn').addEventListener('click', toggle);
  g('ub-close').addEventListener('click', toggle);
  g('ub-send').addEventListener('click', send);
  g('ub-inp').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  restore();
  if (msgs.length === 0) {
    addMsg('bot', '👋 Bonjour ! Je suis UniBot, ton assistant UniSchedule. Comment puis-je t’aider ?');
  }
})();
</script>"""

    script = (_TMPL
              .replace("__SK__",  json.dumps(sk))
              .replace("__KEY__", json.dumps(api_key))
              .replace("__SYS__", json.dumps(system_prompt)))

    _components.html(script, height=0)
