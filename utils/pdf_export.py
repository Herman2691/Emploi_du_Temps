# utils/pdf_export.py
from fpdf import FPDF
from datetime import datetime, timedelta, time as dt_time

DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

# Palette de couleurs (R, G, B)
_DARK_BLUE  = (30,  64,  175)
_BLUE       = (37,  99,  235)
_LIGHT_BLUE = (239, 246, 255)
_AMBER      = (245, 158,  11)
_MUTED      = (100, 116, 139)
_BORDER     = (226, 232, 240)
_ALT_ROW    = (248, 250, 252)
_WHITE      = (255, 255, 255)
_CYAN       = ( 14, 165, 233)


def _fmt(t) -> str:
    if t is None:
        return "--:--"
    if isinstance(t, timedelta):
        total = int(t.total_seconds())
        h, m  = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    if isinstance(t, dt_time):
        return t.strftime("%H:%M")
    return str(t)[:5]


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len - 2] + ".."


def generate_schedule_pdf(
    class_name: str,
    promotion_name: str,
    department_name: str,
    faculty_name: str,
    university_name: str,
    schedules: list,
    week_filter: str = "Toutes",
) -> bytes:
    """Génère un PDF A4 paysage de l'emploi du temps. Retourne les bytes du PDF."""

    # ── Filtrage semaines ────────────────────────────────────────────────────
    if week_filter != "Toutes":
        schedules = [
            s for s in schedules
            if s.get("week_type") in ("Toutes", week_filter)
        ]

    # ── Construction de la grille ────────────────────────────────────────────
    time_slots = sorted(set(
        (_fmt(s["start_time"]), _fmt(s["end_time"]))
        for s in schedules
    ))
    grid = {slot: {day: [] for day in DAYS} for slot in time_slots}
    for s in schedules:
        slot = (_fmt(s["start_time"]), _fmt(s["end_time"]))
        if s["day"] in DAYS and slot in grid:
            grid[slot][s["day"]].append(s)

    # ── Initialisation PDF ───────────────────────────────────────────────────
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(10, 10, 10)

    W = pdf.w - 20          # largeur utile : ~277 mm
    LEFT = 10

    # ════════════════════════════════════════════════════════════════════════
    # EN-TÊTE
    # ════════════════════════════════════════════════════════════════════════

    # Barre titre
    pdf.set_fill_color(*_DARK_BLUE)
    pdf.set_text_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_x(LEFT)
    pdf.cell(W, 11, "EMPLOI DU TEMPS", border=0, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    # Barre université / faculté / département
    pdf.set_fill_color(*_BLUE)
    pdf.set_font("Helvetica", "", 8)
    info = f"{university_name}   |   {faculty_name}   |   {department_name}"
    pdf.set_x(LEFT)
    pdf.cell(W, 6, _truncate(info, 90), border=0, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    # Barre classe
    pdf.set_fill_color(*_AMBER)
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 10)
    class_info = f"Classe {class_name}   -   {promotion_name}"
    pdf.set_x(LEFT)
    pdf.cell(W, 7, class_info, border=0, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    # Ligne méta
    pdf.set_text_color(*_MUTED)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_x(LEFT)
    pdf.cell(
        W, 5,
        f"Semaines : {week_filter}   |   "
        f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(3)

    # ════════════════════════════════════════════════════════════════════════
    # GRILLE HORAIRE
    # ════════════════════════════════════════════════════════════════════════
    time_col_w = 22.0
    day_col_w  = (W - time_col_w) / len(DAYS)

    table_top   = pdf.get_y()
    available_h = pdf.h - table_top - 12   # 12 mm réservés pour le pied de page

    if time_slots:
        row_h = max(11.0, min(27.0, (available_h - 9) / len(time_slots)))
    else:
        row_h = 14.0

    # ── En-tête de la table ──────────────────────────────────────────────────
    pdf.set_fill_color(*_DARK_BLUE)
    pdf.set_text_color(*_WHITE)
    pdf.set_draw_color(*_BORDER)
    pdf.set_font("Helvetica", "B", 8)

    pdf.set_x(LEFT)
    pdf.cell(time_col_w, 9, "Horaire", border=1, align="C", fill=True)
    for day in DAYS:
        pdf.cell(day_col_w, 9, day, border=1, align="C", fill=True)
    pdf.ln(9)

    # ── Pas de cours ─────────────────────────────────────────────────────────
    if not time_slots:
        pdf.set_text_color(*_MUTED)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_x(LEFT)
        pdf.cell(W, 20, "Aucun cours planifie pour cette periode.", align="C")
    else:
        # ── Lignes de données ─────────────────────────────────────────────────
        for row_idx, (start, end) in enumerate(time_slots):
            y_row  = pdf.get_y()
            row_bg = _ALT_ROW if row_idx % 2 == 0 else _WHITE

            # Cellule horaire
            pdf.set_fill_color(*row_bg)
            pdf.set_draw_color(*_BORDER)
            pdf.rect(LEFT, y_row, time_col_w, row_h, style="FD")

            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*_MUTED)
            mid = y_row + row_h / 2 - 4
            pdf.set_xy(LEFT, mid)
            pdf.cell(time_col_w, 4, start, align="C")
            pdf.set_xy(LEFT, mid + 4)
            pdf.cell(time_col_w, 4, end,   align="C")

            # Cellules par jour
            x = LEFT + time_col_w
            for day in DAYS:
                courses = grid[(start, end)][day]

                if not courses:
                    pdf.set_fill_color(*row_bg)
                    pdf.rect(x, y_row, day_col_w, row_h, style="FD")
                else:
                    # Fond bleu clair
                    pdf.set_fill_color(*_LIGHT_BLUE)
                    pdf.rect(x, y_row, day_col_w, row_h, style="FD")
                    # Barre d'accent bleue à gauche
                    pdf.set_fill_color(*_BLUE)
                    pdf.rect(x, y_row, 1.8, row_h, style="F")

                    c    = courses[0]
                    tx   = x + 2.8
                    tw   = day_col_w - 3.5

                    # Nom du cours
                    pdf.set_font("Helvetica", "B", 6.8)
                    pdf.set_text_color(*_DARK_BLUE)
                    pdf.set_xy(tx, y_row + 1.5)
                    pdf.cell(tw, 3.8, _truncate(c["course_name"], 23))

                    # Professeur
                    pdf.set_font("Helvetica", "", 6.2)
                    pdf.set_text_color(*_MUTED)
                    pdf.set_xy(tx, y_row + 5.5)
                    pdf.cell(tw, 3.5, _truncate(c.get("professor_name", ""), 23))

                    # Salle
                    pdf.set_font("Helvetica", "", 5.8)
                    pdf.set_text_color(*_CYAN)
                    pdf.set_xy(tx, y_row + 9.2)
                    room = c.get("room") or "-"
                    pdf.cell(tw, 3.2, f"Salle : {_truncate(room, 18)}")

                    # Indicateur si plusieurs cours
                    if len(courses) > 1:
                        pdf.set_font("Helvetica", "I", 5.2)
                        pdf.set_text_color(*_MUTED)
                        pdf.set_xy(tx, y_row + row_h - 4)
                        pdf.cell(tw, 3, f"+{len(courses) - 1} autre(s)")

                x += day_col_w

            pdf.set_y(y_row + row_h)

    # ════════════════════════════════════════════════════════════════════════
    # PIED DE PAGE
    # ════════════════════════════════════════════════════════════════════════
    pdf.set_y(pdf.h - 10)
    pdf.set_draw_color(*_BLUE)
    pdf.line(LEFT, pdf.h - 11, pdf.w - 10, pdf.h - 11)
    pdf.set_text_color(*_MUTED)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_x(LEFT)
    pdf.cell(
        W, 5,
        "UniSchedule  -  Plateforme de gestion des emplois du temps universitaires",
        align="C",
    )

    return bytes(pdf.output())


def generate_bulletin_pdf(
    student_name: str,
    student_number: str,
    class_name: str,
    promotion_name: str,
    university_name: str,
    session_name: str,
    grades_by_course: dict,
    overall_avg: float,
    mention: str,
    rank=None,
) -> bytes:
    """Génère un bulletin de notes A4 portrait. Retourne les bytes du PDF."""

    _GREEN  = (16,  185, 129)
    _VIOLET = (124,  58, 237)
    _RED    = (239,  68,  68)
    _AMBER  = (245, 158,  11)
    _GRAY   = (100, 116, 139)
    _LIGHT  = (248, 250, 252)
    _BORDER = (226, 232, 240)
    _DARK   = (30,   41,  59)
    _WHITE  = (255, 255, 255)
    _BLUE   = (37,   99, 235)

    def _avg_color(avg):
        if avg >= 16: return _VIOLET
        if avg >= 14: return _GREEN
        if avg >= 10: return _AMBER
        return _RED

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    W = 180  # largeur utile

    # ── En-tête ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(*_BLUE)
    pdf.rect(0, 0, 210, 32, style="F")
    pdf.set_y(6)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*_WHITE)
    pdf.cell(210, 8, "BULLETIN DE NOTES", align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(210, 5, university_name, align="C", ln=True)
    pdf.set_y(35)
    pdf.set_text_color(*_DARK)

    # ── Infos étudiant ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*_LIGHT)
    pdf.cell(W, 7, "  INFORMATIONS ÉTUDIANT", fill=True, ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_GRAY)
    _infos = [
        ("Étudiant",   student_name),
        ("N° Étudiant", student_number),
        ("Classe",     class_name),
        ("Promotion",  promotion_name),
        ("Session",    session_name),
    ]
    for _k, _v in _infos:
        pdf.cell(40, 5.5, f"  {_k} :", ln=False)
        pdf.set_text_color(*_DARK)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(W - 40, 5.5, _v, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_GRAY)
    pdf.ln(3)

    # ── Résumé ─────────────────────────────────────────────────────────────────
    avg_c = _avg_color(overall_avg)
    pdf.set_fill_color(*[int(x * 0.12 + 248 * 0.88) for x in avg_c])
    pdf.set_draw_color(*avg_c)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*_DARK)
    pdf.cell(W, 7, "  RÉSUMÉ", fill=True, border="B", ln=True)

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*avg_c)
    pdf.cell(W / 2, 12, f"{overall_avg:.2f}/20", align="C", ln=False)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(W / 2, 12, mention, align="C", ln=True)
    if rank is not None:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_GRAY)
        pdf.cell(W, 5, f"Rang dans la classe : {rank}", align="C", ln=True)
    pdf.ln(3)

    # ── Tableau des notes ──────────────────────────────────────────────────────
    pdf.set_fill_color(*_BLUE)
    pdf.set_text_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 9)
    _col_w = [70, 35, 22, 22, 31]
    _headers = ["Cours", "Type d'épreuve", "Note", "/Max", "Moyenne /20"]
    for _h, _cw in zip(_headers, _col_w):
        pdf.cell(_cw, 7, f" {_h}", fill=True, border=1)
    pdf.ln()

    pdf.set_text_color(*_DARK)
    _fill = False
    for _cn, _data in sorted(grades_by_course.items()):
        for _exam in _data["exams"]:
            pdf.set_fill_color(*(_LIGHT if _fill else _WHITE))
            pdf.set_font("Helvetica", "", 8)
            _avg20 = _data["avg20"]
            _nc    = _avg_color(_avg20)
            _row = [
                _truncate(_cn, 38),
                _truncate(_exam["type"], 20),
                f"{_exam['grade']:.1f}",
                f"{_exam['max']:.0f}",
                f"{_avg20:.2f}/20",
            ]
            for _i, (_v, _cw) in enumerate(zip(_row, _col_w)):
                if _i == 4:
                    pdf.set_text_color(*_nc)
                    pdf.set_font("Helvetica", "B", 8)
                pdf.cell(_cw, 6, f" {_v}", fill=True, border=1)
                pdf.set_text_color(*_DARK)
                pdf.set_font("Helvetica", "", 8)
            pdf.ln()
            _fill = not _fill

    # ── Pied de page ───────────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*_GRAY)
    pdf.cell(W, 5,
             f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} · UniSchedule",
             align="C")

    return bytes(pdf.output())
