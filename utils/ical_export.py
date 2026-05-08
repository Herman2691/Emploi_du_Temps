# utils/ical_export.py
from datetime import datetime, date, timedelta, time as dt_time
import uuid


def _to_time(t) -> dt_time:
    if isinstance(t, dt_time):
        return t
    if isinstance(t, timedelta):
        s = int(t.total_seconds())
        return dt_time(s // 3600, (s % 3600) // 60)
    return dt_time(0, 0)


_DAY_OFFSET = {
    "Lundi": 0, "Mardi": 1, "Mercredi": 2,
    "Jeudi": 3, "Vendredi": 4, "Samedi": 5
}


def generate_ical(schedules: list, class_name: str,
                  university_name: str = "") -> bytes:
    today = date.today()
    monday0 = today - timedelta(days=today.weekday())
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//UniSchedule//FR",
        f"X-WR-CALNAME:{class_name} - {university_name}",
        "X-WR-TIMEZONE:Africa/Kinshasa",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for s in schedules:
        day_off = _DAY_OFFSET.get(s.get("day", "Lundi"), 0)
        st = _to_time(s["start_time"])
        et = _to_time(s["end_time"])
        vf = s.get("valid_from")
        vu = s.get("valid_until")
        slot_type = s.get("slot_type", "cours")
        status = s.get("slot_status", "actif")
        if status == "annule":
            continue

        summary = s.get("course_name", "Cours")
        if slot_type == "examen":
            summary = f"EXAMEN - {summary}"
        elif slot_type == "ferie":
            summary = f"FERIE - {summary}"

        sub = s.get("substitute_name")
        prof = s.get("professor_name", "")
        desc = f"Prof: {sub or prof}" if (sub or prof) else ""
        location = s.get("room", "") or ""

        if vf and vu and vf == vu:
            # Single-day event (exam/ferie) — use monday of valid_from week + day_offset
            week_monday = vf - timedelta(days=vf.weekday())
            event_date = week_monday + timedelta(days=day_off)
            dtstart = datetime.combine(event_date, st).strftime("%Y%m%dT%H%M%S")
            dtend = datetime.combine(event_date, et).strftime("%Y%m%dT%H%M%S")
            lines += _vevent(summary, dtstart, dtend, desc, location)
        else:
            # Recurring — generate for next 16 weeks
            week_type = s.get("week_type", "Toutes")
            for w in range(16):
                wk_monday = monday0 + timedelta(weeks=w)
                event_date = wk_monday + timedelta(days=day_off)
                if vf and event_date < vf:
                    continue
                if vu and event_date > vu:
                    continue
                wk_num = wk_monday.isocalendar()[1]
                if week_type == "Paire" and wk_num % 2 != 0:
                    continue
                if week_type == "Impaire" and wk_num % 2 == 0:
                    continue
                dtstart = datetime.combine(event_date, st).strftime("%Y%m%dT%H%M%S")
                dtend = datetime.combine(event_date, et).strftime("%Y%m%dT%H%M%S")
                lines += _vevent(summary, dtstart, dtend, desc, location)

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines).encode("utf-8")


def _vevent(summary, dtstart, dtend, description, location):
    return [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@unischedule",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{location}",
        "END:VEVENT",
    ]
