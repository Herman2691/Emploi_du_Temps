# utils/notifications.py
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ── Config SMTP (secrets.toml section [email]) ───────────────────────────────
def _cfg():
    try:
        e = st.secrets.get("email", {})
        return {
            "host":     e.get("smtp_host",     "smtp.gmail.com"),
            "port":     int(e.get("smtp_port", 587)),
            "user":     e.get("smtp_user",     ""),
            "password": e.get("smtp_password", ""),
            "sender":   e.get("sender_name",   "UniSchedule"),
        }
    except Exception:
        return None


def _send(addresses: list, subject: str, html: str) -> int:
    """Envoie un email HTML à une liste d'adresses. Retourne le nombre envoyé."""
    cfg = _cfg()
    if not cfg or not cfg["user"] or not cfg["password"]:
        return 0   # Email non configuré → skip silencieux

    sent = 0
    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as srv:
            srv.starttls()
            srv.login(cfg["user"], cfg["password"])
            for addr in addresses:
                if not addr:
                    continue
                msg            = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"]    = f"{cfg['sender']} <{cfg['user']}>"
                msg["To"]      = addr
                msg.attach(MIMEText(html, "html", "utf-8"))
                srv.sendmail(cfg["user"], addr, msg.as_string())
                sent += 1
    except Exception:
        pass
    return sent


# ── Templates HTML ───────────────────────────────────────────────────────────
def _header(university: str, gradient: str) -> str:
    return f"""
    <div style="background:{gradient};padding:1.5rem;
                border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:white;margin:0;font-size:1.4rem">🎓 UniSchedule</h1>
        <p style="color:rgba(255,255,255,0.8);margin:0.25rem 0 0;font-size:0.82rem">
            {university}
        </p>
    </div>"""


def _footer() -> str:
    return """
    <hr style="border:none;border-top:1px solid #E2E8F0;margin:1.5rem 0">
    <p style="color:#94A3B8;font-size:0.72rem;text-align:center;margin:0">
        UniSchedule · Connectez-vous à votre espace étudiant pour plus d'informations.
    </p>"""


def _wrap(inner: str) -> str:
    return (
        f'<div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto">'
        f'{inner}'
        f'</div>'
    )


def _announcement_html(title, content, university, department):
    return _wrap(
        _header(university, "linear-gradient(135deg,#1E40AF,#2563EB)")
        + f"""
        <div style="background:white;border:1px solid #E2E8F0;border-top:none;
                    padding:2rem;border-radius:0 0 12px 12px">
            <p style="color:#64748B;font-size:0.8rem;margin:0 0 1rem">
                📢 Nouveau communiqué — {department}
            </p>
            <h2 style="color:#1E293B;margin:0 0 1rem;font-size:1.15rem">{title}</h2>
            <p style="color:#475569;line-height:1.6;margin:0">{content}</p>
            {_footer()}
        </div>"""
    )


def _tp_html(tp_title, course, deadline_str, description, university):
    desc_block = (
        f"<p style='color:#475569;line-height:1.6;margin:0 0 1rem'>{description}</p>"
        if description else ""
    )
    return _wrap(
        _header(university, "linear-gradient(135deg,#065F46,#10B981)")
        + f"""
        <div style="background:white;border:1px solid #E2E8F0;border-top:none;
                    padding:2rem;border-radius:0 0 12px 12px">
            <p style="color:#64748B;font-size:0.8rem;margin:0 0 1rem">
                📝 Nouveau TP — {course}
            </p>
            <h2 style="color:#1E293B;margin:0 0 1rem;font-size:1.15rem">{tp_title}</h2>
            <div style="background:#FEF3C7;border-left:4px solid #F59E0B;
                        padding:0.75rem 1rem;border-radius:0 8px 8px 0;margin:0 0 1rem">
                <strong style="color:#92400E">⏰ Deadline : {deadline_str}</strong>
            </div>
            {desc_block}
            <p style="color:#64748B;font-size:0.875rem">
                Déposez votre travail en PDF depuis votre espace étudiant avant la deadline.
            </p>
            {_footer()}
        </div>"""
    )


def _grade_html(student_name, course, grade, max_grade, exam_type, comment, university):
    pct   = grade / max_grade * 100 if max_grade else 0
    color = "#10B981" if pct >= 70 else "#F59E0B" if pct >= 50 else "#EF4444"
    cmnt_block = (
        f"<div style='background:#F8FAFC;border-radius:8px;padding:0.75rem 1rem;"
        f"margin:1rem 0'><p style='color:#475569;margin:0;font-size:0.875rem'>"
        f"💬 {comment}</p></div>"
        if comment else ""
    )
    return _wrap(
        _header(university, "linear-gradient(135deg,#1E40AF,#7C3AED)")
        + f"""
        <div style="background:white;border:1px solid #E2E8F0;border-top:none;
                    padding:2rem;border-radius:0 0 12px 12px">
            <p style="color:#64748B;font-size:0.8rem;margin:0 0 1rem">
                📊 Note publiée — {course}
            </p>
            <h2 style="color:#1E293B;margin:0 0 0.5rem;font-size:1.1rem">
                Bonjour {student_name},
            </h2>
            <p style="color:#475569;margin:0 0 1.5rem">
                Votre note pour <strong>{exam_type}</strong> en
                <strong>{course}</strong> a été publiée.
            </p>
            <div style="text-align:center;margin:1.5rem 0">
                <span style="font-size:3rem;font-weight:800;color:{color};
                             font-family:Georgia,serif">
                    {grade:.1f}
                </span>
                <span style="font-size:1.1rem;color:#94A3B8">/{max_grade:.0f}</span>
            </div>
            {cmnt_block}
            {_footer()}
        </div>"""
    )


# ── Fonctions publiques ───────────────────────────────────────────────────────
def notify_announcement_dept(dept_id: int, title: str, content: str,
                              university_name: str, department_name: str) -> int:
    """Notifie tous les étudiants d'un département d'un nouveau communiqué."""
    try:
        from db.queries import PromotionQueries, ClassQueries, StudentQueries
        emails = []
        for promo in PromotionQueries.get_by_department(dept_id):
            for cls in ClassQueries.get_by_promotion(promo["id"]):
                for stu in StudentQueries.get_by_class(cls["id"]):
                    if stu.get("email"):
                        emails.append(stu["email"])
        emails = list(set(emails))
        if not emails:
            return 0
        html = _announcement_html(title, content, university_name, department_name)
        return _send(emails, f"[UniSchedule] {title}", html)
    except Exception:
        return 0


def notify_tp(class_id: int, tp_title: str, course_name: str,
               deadline_str: str, description: str, university_name: str) -> int:
    """Notifie les étudiants d'une classe d'un nouveau TP."""
    try:
        from db.queries import StudentQueries
        students = StudentQueries.get_by_class(class_id)
        emails   = [s["email"] for s in students if s.get("email")]
        if not emails:
            return 0
        html = _tp_html(tp_title, course_name, deadline_str, description, university_name)
        return _send(emails, f"[UniSchedule] Nouveau TP : {tp_title}", html)
    except Exception:
        return 0


def notify_grade(student_email: str, student_name: str, course_name: str,
                  grade: float, max_grade: float, exam_type: str,
                  comment: str, university_name: str) -> bool:
    """Notifie un étudiant de sa note publiée."""
    if not student_email:
        return False
    try:
        html = _grade_html(student_name, course_name, grade, max_grade,
                           exam_type, comment, university_name)
        return _send([student_email], f"[UniSchedule] Note — {course_name}", html) > 0
    except Exception:
        return False


def notify_session_published(grades: list, session_name: str,
                              university: str = "UniSchedule") -> int:
    """Envoie un email récapitulatif à chaque étudiant dont les notes sont publiées."""
    from collections import defaultdict
    by_student: dict = defaultdict(list)
    for g in grades:
        email = g.get("student_email") or g.get("email")
        if email:
            by_student[(email, g.get("student_name", "Étudiant"))].append(g)

    sent = 0
    for (email, name), student_grades in by_student.items():
        rows = ""
        for g in student_grades:
            val = g.get("grade", 0) or 0
            mx  = g.get("max_grade", 20) or 20
            pct = val / mx * 100 if mx else 0
            color = "#10B981" if pct >= 70 else "#F59E0B" if pct >= 50 else "#EF4444"
            rows += (
                f"<tr>"
                f"<td style='padding:0.5rem;border-bottom:1px solid #E2E8F0'>{g.get('course_name','')}</td>"
                f"<td style='padding:0.5rem;border-bottom:1px solid #E2E8F0'>{g.get('exam_type','')}</td>"
                f"<td style='padding:0.5rem;border-bottom:1px solid #E2E8F0;text-align:center;"
                f"font-weight:700;color:{color}'>{val:.1f}/{mx:.0f}</td>"
                f"</tr>"
            )
        html = _wrap(
            _header(university, "linear-gradient(135deg,#1E40AF,#7C3AED)")
            + f"""
            <div style="background:white;border:1px solid #E2E8F0;border-top:none;
                        padding:2rem;border-radius:0 0 12px 12px">
                <h2 style="color:#1E293B;margin:0 0 0.5rem;font-size:1.1rem">
                    Bonjour {name},
                </h2>
                <p style="color:#475569;margin:0 0 1.5rem">
                    Vos résultats pour la session <strong>{session_name}</strong>
                    ont été publiés.
                </p>
                <table style="width:100%;border-collapse:collapse;font-size:0.875rem">
                    <thead>
                        <tr style="background:#F8FAFC">
                            <th style="padding:0.5rem;text-align:left;color:#64748B">Cours</th>
                            <th style="padding:0.5rem;text-align:left;color:#64748B">Type</th>
                            <th style="padding:0.5rem;text-align:center;color:#64748B">Note</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                {_footer()}
            </div>"""
        )
        if _send([email], f"[UniSchedule] Résultats {session_name}", html) > 0:
            sent += 1
    return sent


def notify_at_risk(student_data: list, session_name: str,
                   university: str = "UniSchedule") -> int:
    """
    Notifie les étudiants à risque de leur situation.
    student_data : liste de dicts avec keys email, student_name, average, decision.
    """
    sent = 0
    for stu in student_data:
        email = stu.get("email")
        if not email:
            continue
        name     = stu.get("student_name", "Étudiant")
        avg      = stu.get("average", 0) or 0
        decision = stu.get("decision", "")
        color    = "#D97706" if decision == "Session 2" else "#DC2626"
        icon     = "⚠️" if decision == "Session 2" else "❌"
        msg = (
            "Vous êtes admis(e) en session de rattrapage (Session 2)."
            if decision == "Session 2"
            else "Vous êtes ajourné(e) pour cette session."
        )
        html = _wrap(
            _header(university, f"linear-gradient(135deg,{color},{color}99)")
            + f"""
            <div style="background:white;border:1px solid #E2E8F0;border-top:none;
                        padding:2rem;border-radius:0 0 12px 12px">
                <h2 style="color:#1E293B;margin:0 0 0.5rem;font-size:1.1rem">
                    Bonjour {name},
                </h2>
                <p style="color:#475569;margin:0 0 1.5rem">
                    Vos résultats pour la session <strong>{session_name}</strong>
                    ont été analysés.
                </p>
                <div style="background:{color}15;border-left:4px solid {color};
                            padding:1rem 1.25rem;border-radius:0 8px 8px 0;
                            margin-bottom:1.5rem">
                    <div style="font-size:1.5rem;font-weight:700;color:{color}">
                        {icon} {decision}
                    </div>
                    <div style="color:{color};font-size:0.9rem;margin-top:0.25rem">
                        Moyenne : <strong>{float(avg):.2f}/20</strong>
                    </div>
                    <p style="color:#475569;margin:0.75rem 0 0;font-size:0.875rem">
                        {msg}
                    </p>
                </div>
                <p style="color:#64748B;font-size:0.875rem">
                    Consultez votre espace étudiant pour le détail de vos notes
                    et contactez votre département pour plus d'informations.
                </p>
                {_footer()}
            </div>"""
        )
        if _send([email], f"[{university}] Résultats session {session_name} — {icon} {decision}", html) > 0:
            sent += 1
    return sent


def notify_schedule_change(class_name: str, day: str, start_time: str,
                            course_name: str, change_type: str,
                            note: str, student_emails: list,
                            university: str = "UniSchedule") -> int:
    """Notifie les étudiants d'une modification d'horaire (annulation, remplacement, etc.)."""
    subject = f"[{university}] Modification d'horaire — {class_name}"
    color = {
        "annule":   "#DC2626",
        "remplace": "#D97706",
        "update":   "#2563EB",
    }.get(change_type, "#2563EB")
    label = {
        "annule":   "Cours annulé",
        "remplace": "Cours remplacé",
        "update":   "Horaire modifié",
    }.get(change_type, "Modification")
    note_html = f"<p><b>Note :</b> {note}</p>" if note else ""
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:auto">
      <div style="background:{color};color:white;padding:1rem;border-radius:8px 8px 0 0">
        <h2 style="margin:0">{label}</h2>
        <p style="margin:0.3rem 0 0;opacity:0.85">{university}</p>
      </div>
      <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:1.25rem;border-radius:0 0 8px 8px">
        <p><b>Classe :</b> {class_name}</p>
        <p><b>Cours :</b> {course_name}</p>
        <p><b>Jour :</b> {day} à {start_time}</p>
        {note_html}
      </div>
    </div>"""
    return _send(student_emails, subject, html)
