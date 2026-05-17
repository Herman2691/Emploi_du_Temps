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


def generate_bulletin_pdf_ue(
    student_name: str,
    student_number: str,
    class_name: str,
    promotion_name: str,
    university_name: str,
    session_name: str,
    ue_map: dict,
    by_group: dict,
    group_avgs: dict,
    total_avg: float,
    obtained_credits: float,
    total_ue_credits: float,
    ecs_a_reprendre: int,
    final_decision: str,
    mention: str,
    rank=None,
    faculty_name: str = "",
    department_name: str = "",
) -> bytes:
    """Génère un bulletin UE/EC au format académique (analogue bulletin.jpeg). Retourne bytes PDF."""

    _GREEN  = (16,  185, 129)
    _RED    = (239,  68,  68)
    _AMBER  = (245, 158,  11)
    _GRAY   = (100, 116, 139)
    _LIGHT  = (248, 250, 252)
    _BORDER = (226, 232, 240)
    _DARK   = (30,   41,  59)
    _WHITE  = (255, 255, 255)
    _BLUE   = (37,   99, 235)
    _DKBLUE = (30,   64, 175)
    _LBLUE  = (239, 246, 255)
    _VIOLET = (124,  58, 237)

    def _nc(val):
        if val >= 16: return _VIOLET
        if val >= 14: return _GREEN
        if val >= 10: return _AMBER
        return _RED

    def _cell(pdf, w, h, txt, fill=False, border=1, align="L", bold=False, sz=8,
               color=None, bg=None):
        if bg:
            pdf.set_fill_color(*bg)
        if color:
            pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B" if bold else "", sz)
        pdf.cell(w, h, txt, border=border, fill=fill, align=align)
        pdf.set_text_color(*_DARK)

    # ── Extraire l'année académique depuis session_name ──────────────────────
    import re as _re
    _ay_match = _re.search(r"\d{4}[-/]\d{4}", session_name)
    _annee_acad = _ay_match.group(0) if _ay_match else ""

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_margins(12, 12, 12)
    W = 186  # largeur utile (210 - 24)

    # ── En-tête ────────────────────────────────────────────────────────────────
    # Calculer la hauteur de l'en-tête selon les informations disponibles
    _header_lines = 2  # université + secrétariat
    if faculty_name:
        _header_lines += 1
    if department_name:
        _header_lines += 1
    _header_lines += 2  # promotion+session + année académique
    _header_h = 10 + _header_lines * 5

    pdf.set_fill_color(*_DKBLUE)
    pdf.rect(0, 0, 210, _header_h, style="F")
    pdf.set_y(5)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*_WHITE)
    pdf.cell(210, 7, university_name.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(210, 5, "SÉCRÉTARIAT GÉNÉRAL ACADÉMIQUE", align="C", new_x="LMARGIN", new_y="NEXT")
    if faculty_name:
        pdf.cell(210, 5, f"FACULTÉ : {faculty_name.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
    if department_name:
        pdf.cell(210, 5, f"DÉP/OPTION : {department_name.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
    _sess_upper = session_name.upper()
    # Extraire la partie session courte (ex: "S1 NORMALE") du nom complet
    _sess_parts = _sess_upper.split()
    _sess_label = " ".join(p for p in _sess_parts if not _re.match(r"\d{4}[-/]\d{4}", p)).strip()
    if not _sess_label:
        _sess_label = _sess_upper
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(210, 5, f"{promotion_name.upper()}, SESSION {_sess_label}", align="C", new_x="LMARGIN", new_y="NEXT")
    if _annee_acad:
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(210, 5, f"ANNEE ACADEMIQUE {_annee_acad}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(_header_h + 4)
    pdf.set_text_color(*_DARK)

    # ── Infos étudiant ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*_LIGHT)
    pdf.cell(W, 6, "  INFORMATIONS ÉTUDIANT", fill=True, new_x="LMARGIN", new_y="NEXT")
    _infos = [
        ("Nom & Prénoms", student_name),
        ("N° Matricule",  student_number),
        ("Classe",        class_name),
        ("Promotion",     promotion_name),
        ("Mention",       mention),
    ]
    if rank is not None:
        _infos.append(("Rang", str(rank)))
    pdf.set_font("Helvetica", "", 8)
    for _k, _v in _infos:
        pdf.set_text_color(*_GRAY)
        pdf.cell(42, 5, f"  {_k} :", new_x="RIGHT")
        pdf.set_text_color(*_DARK)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(W - 42, 5, _v, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
    pdf.ln(3)

    # ── En-tête du tableau ─────────────────────────────────────────────────────
    _CW = [22, 72, 16, 18, 22, 22, 14]  # Code | Intitulé | Crd EC | Crd UE | Note EC | Note UE | Dec
    _HDRS = ["Code", "Intitulé UE / Élément Constitutif", "Crd EC", "Crd UE", "Note EC", "Note UE", "Dec"]

    pdf.set_fill_color(*_DKBLUE)
    pdf.set_text_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 7.5)
    for _h, _cw in zip(_HDRS, _CW):
        pdf.cell(_cw, 7, f" {_h}", border=1, fill=True, align="C")
    pdf.ln()

    # ── Lignes UE / EC ─────────────────────────────────────────────────────────
    for glabel in sorted(by_group.keys()):
        ues_g = sorted(by_group[glabel], key=lambda u: u.get("ue_code", ""))
        for ue in ues_g:
            nue = ue["note_ue"]
            dec = ue["decision"]
            nue_c = _GREEN if nue >= 10 else _RED
            dec_c = _GREEN if dec == "V" else _RED

            # Ligne UE (fond bleu clair, bold)
            pdf.set_fill_color(*_LBLUE)
            pdf.set_text_color(*_DARK)
            pdf.set_font("Helvetica", "B", 8)
            _row_ue = [
                ue.get("ue_code", "") or "",
                _truncate(ue["ue_name"], 36),
                "-",
                f"{ue['ue_credits']:.0f}",
                "-",
                f"{nue:.2f}",
                dec,
            ]
            for _i, (_v, _cw) in enumerate(zip(_row_ue, _CW)):
                if _i == 5:
                    pdf.set_text_color(*nue_c)
                elif _i == 6:
                    pdf.set_text_color(*dec_c)
                else:
                    pdf.set_text_color(*_DARK)
                pdf.cell(_cw, 6, f" {_v}", border=1, fill=True,
                         align="C" if _i != 1 else "L")
            pdf.ln()

            # Lignes EC (indentées, fond blanc, normal)
            pdf.set_fill_color(*_WHITE)
            pdf.set_font("Helvetica", "", 7.5)
            for cn, ec in sorted(ue["courses"].items()):
                ne  = ec["avg20"]
                nec = _GREEN if ne >= 10 else _RED
                _row_ec = [
                    "-",
                    _truncate(f"  {cn}", 38),
                    f"{ec['credits_ec']:.0f}",
                    "-",
                    f"{ne:.2f}",
                    "-",
                    "-",
                ]
                for _i, (_v, _cw) in enumerate(zip(_row_ec, _CW)):
                    if _i == 4:
                        pdf.set_text_color(*nec)
                    else:
                        pdf.set_text_color(*_GRAY if _i != 1 else _DARK)
                    pdf.cell(_cw, 5.5, f" {_v}" if _i != 1 else _v, border=1,
                             fill=True, align="C" if _i != 1 else "L")
                pdf.ln()
                pdf.set_text_color(*_DARK)

    # ── Lignes de synthèse par groupe ──────────────────────────────────────────
    pdf.set_fill_color(*_LIGHT)
    pdf.set_font("Helvetica", "B", 8)
    for glabel in sorted(by_group.keys()):
        gavg  = group_avgs.get(glabel, 0)
        gc    = _GREEN if gavg >= 10 else _RED
        _lbl  = f"  Moyenne Groupe {glabel}"
        pdf.set_text_color(*_DARK)
        _span = sum(_CW[:5])
        pdf.cell(_span, 6, _lbl, border=1, fill=True, align="R")
        pdf.set_text_color(*gc)
        pdf.cell(_CW[5], 6, f" {gavg:.2f}", border=1, fill=True, align="C")
        pdf.set_text_color(*_DARK)
        pdf.cell(_CW[6], 6, "", border=1, fill=True)
        pdf.ln()

    # ── Tableau de synthèse RÉSULTATS ─────────────────────────────────────────
    pdf.ln(4)
    _fc  = _GREEN if final_decision == "VAL" else _RED
    _tac = _GREEN if total_avg >= 10 else _RED

    # Titre centré "RÉSULTATS"
    pdf.set_fill_color(*_DKBLUE)
    pdf.set_text_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(W, 7, "RÉSULTATS", border=1, fill=True, align="C",
             new_x="LMARGIN", new_y="NEXT")

    # En-têtes des colonnes de synthèse
    _sorted_groups = sorted(by_group.keys())
    _ncols = len(_sorted_groups)
    # Largeurs : Moy A | Moy B | ... | Moy Totale | Crédits | Nbre EC reprendre | Décision
    _syn_fixed = [28, 35, 25, 18]   # Moy Totale | Crédits | ECs reprendre | Décision
    _syn_group_w = max(10, (W - sum(_syn_fixed)) // max(_ncols, 1)) if _ncols > 0 else 30

    pdf.set_fill_color(*_LBLUE)
    pdf.set_text_color(*_DARK)
    pdf.set_font("Helvetica", "B", 7)
    for _gl in _sorted_groups:
        pdf.cell(_syn_group_w, 6, f" Moy. Gr. {_gl}", border=1, fill=True, align="C")
    pdf.cell(_syn_fixed[0], 6, " Moy. Totale", border=1, fill=True, align="C")
    pdf.cell(_syn_fixed[1], 6, f" Crédits/{total_ue_credits:.0f}", border=1, fill=True, align="C")
    pdf.cell(_syn_fixed[2], 6, " ECs à reprendre", border=1, fill=True, align="C")
    pdf.cell(_syn_fixed[3], 6, " Décision", border=1, fill=True, align="C")
    pdf.ln()

    # Valeurs
    pdf.set_fill_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for _gl in _sorted_groups:
        _ga = group_avgs.get(_gl, 0)
        _gc = _GREEN if _ga >= 10 else _RED
        pdf.set_text_color(*_gc)
        pdf.cell(_syn_group_w, 7, f" {_ga:.2f}", border=1, fill=True, align="C")
    pdf.set_text_color(*_tac)
    pdf.cell(_syn_fixed[0], 7, f" {total_avg:.2f}", border=1, fill=True, align="C")
    pdf.set_text_color(*_DARK)
    pdf.cell(_syn_fixed[1], 7, f" {obtained_credits:.0f}/{total_ue_credits:.0f}", border=1, fill=True, align="C")
    pdf.cell(_syn_fixed[2], 7, f" {ecs_a_reprendre}", border=1, fill=True, align="C")
    pdf.set_text_color(*_fc)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(_syn_fixed[3], 7, f" {final_decision}", border=1, fill=True, align="C")
    pdf.ln()

    # Note explicative
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    if final_decision == "VAL":
        pdf.set_text_color(*_GREEN)
        pdf.cell(W, 5, "VAL = Vous avez validé le semestre",
                 align="L", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(*_RED)
        pdf.cell(W, 5,
                 f"NVAL = Semestre non validé - {ecs_a_reprendre} EC(s) à reprendre",
                 align="L", new_x="LMARGIN", new_y="NEXT")

    # ── Pied de page ───────────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.set_draw_color(*_BLUE)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*_GRAY)
    pdf.cell(W, 5,
             f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} · UniSchedule",
             align="C")

    return bytes(pdf.output())


def generate_enrollment_pdf(
    student_name: str,
    student_number: str,
    university_name: str,
    faculty_name: str,
    department_name: str,
    promotion_name: str,
    filiere_name: str,
    option_name: str,
    academic_year: str,
    session_name: str,
    programme: list,
    class_name: str = "",
) -> bytes:
    """Génère une fiche d'enrôlement PDF pour un étudiant et une session donnée."""

    _DB  = (30, 64, 175)
    _B   = (37, 99, 235)
    _LB  = (239, 246, 255)
    _W   = (255, 255, 255)
    _G   = (100, 116, 139)
    _BRD = (203, 213, 225)
    _ALT = (248, 250, 252)
    _BLK = (15, 23, 42)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    W = pdf.w - 30

    # En-tête université
    pdf.set_fill_color(*_DB)
    pdf.set_text_color(*_W)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(W, 9, university_name.upper(), border=0, fill=True,
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    if faculty_name:
        pdf.set_fill_color(*_B)
        pdf.cell(W, 5, faculty_name, border=0, fill=True,
                 align="C", new_x="LMARGIN", new_y="NEXT")
    if department_name:
        pdf.set_fill_color(*_B)
        pdf.cell(W, 5, department_name, border=0, fill=True,
                 align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Titre
    pdf.set_text_color(*_DB)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(W, 8, "FICHE D'ENROLEMENT", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*_B)
    pdf.cell(W, 6, session_name.upper(), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Infos étudiant
    pdf.set_draw_color(*_BRD)
    pdf.set_text_color(*_BLK)

    def _row(label, value):
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*_LB)
        pdf.cell(45, 6, f"  {label} :", border=1, fill=True, align="L")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(*_W)
        pdf.cell(W - 45, 6, f"  {value or '-'}", border=1, fill=True, align="L",
                 new_x="LMARGIN", new_y="NEXT")

    _row("Nom et Prenom", student_name)
    _row("N Matricule", student_number)
    _row("Promotion", promotion_name)
    if filiere_name:
        _row("Filiere", filiere_name)
    if option_name:
        _row("Option", option_name)
    if class_name:
        _row("Classe", class_name)
    _row("Annee academique", academic_year or "-")
    pdf.ln(5)

    # Tableau programme
    _groups = {}
    for _c in programme:
        _grp = _c.get("ue_group") or "-"
        _ue_key = (_c.get("ue_id"), _c.get("ue_code") or "",
                   _c.get("ue_name") or "", float(_c.get("ue_credits") or 0))
        _groups.setdefault(_grp, {}).setdefault(_ue_key, []).append(_c)

    _sorted_g = sorted(_groups.keys())
    _sess_lbl = {g: f"Session {i+1}" for i, g in enumerate(_sorted_g)}
    _CW = [22, 90, 22, 22, 34]

    for _grp in _sorted_g:
        _lbl = _sess_lbl.get(_grp, _grp).upper()
        pdf.set_fill_color(*_DB)
        pdf.set_text_color(*_W)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(sum(_CW), 7, f"  UE DU {_lbl}",
                 border=1, fill=True, align="L", new_x="LMARGIN", new_y="NEXT")

        pdf.set_fill_color(*_B)
        pdf.set_font("Helvetica", "B", 7)
        for _h, _w in zip(["Code UE", "Intitules UE / EC", "Cr. EC", "Cr. UE", "Professeur"], _CW):
            pdf.cell(_w, 6, f" {_h}", border=1, fill=True, align="C")
        pdf.ln()

        _alt = False
        for (_uid, _ucode, _uname, _ucred), _courses in sorted(
            _groups[_grp].items(), key=lambda x: (x[0][1], x[0][2])
        ):
            if _uid:
                pdf.set_fill_color(*_LB)
                pdf.set_text_color(*_DB)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.cell(_CW[0], 6, f" {_ucode or '-'}", border=1, fill=True, align="C")
                pdf.cell(_CW[1], 6, f" {_uname}", border=1, fill=True, align="L")
                pdf.cell(_CW[2], 6, " -", border=1, fill=True, align="C")
                pdf.cell(_CW[3], 6, f" {int(_ucred) if _ucred else '-'}",
                         border=1, fill=True, align="C")
                pdf.cell(_CW[4], 6, " -", border=1, fill=True, align="C")
                pdf.ln()
                for _ec in _courses:
                    _bg = _ALT if _alt else _W
                    pdf.set_fill_color(*_bg)
                    pdf.set_text_color(*_BLK)
                    pdf.set_font("Helvetica", "", 7)
                    _cr = _ec.get("credits_ec")
                    pdf.cell(_CW[0], 5.5, " -", border=1, fill=True, align="C")
                    pdf.cell(_CW[1], 5.5, f"    -> {_ec['name']}", border=1, fill=True, align="L")
                    pdf.cell(_CW[2], 5.5, f" {int(_cr) if _cr else '-'}",
                             border=1, fill=True, align="C")
                    pdf.cell(_CW[3], 5.5, " -", border=1, fill=True, align="C")
                    pdf.cell(_CW[4], 5.5, f" {_ec.get('professor_name') or '-'}",
                             border=1, fill=True, align="L")
                    pdf.ln()
                    _alt = not _alt
            else:
                for _ec in _courses:
                    _bg = _ALT if _alt else _W
                    pdf.set_fill_color(*_bg)
                    pdf.set_text_color(*_BLK)
                    pdf.set_font("Helvetica", "", 7)
                    _cr = _ec.get("credits_ec")
                    pdf.cell(_CW[0], 5.5, " -", border=1, fill=True, align="C")
                    pdf.cell(_CW[1], 5.5, f" {_ec['name']}", border=1, fill=True, align="L")
                    pdf.cell(_CW[2], 5.5, f" {int(_cr) if _cr else '-'}",
                             border=1, fill=True, align="C")
                    pdf.cell(_CW[3], 5.5, " -", border=1, fill=True, align="C")
                    pdf.cell(_CW[4], 5.5, f" {_ec.get('professor_name') or '-'}",
                             border=1, fill=True, align="L")
                    pdf.ln()
                    _alt = not _alt
        pdf.ln(3)

    # Zone signatures
    pdf.ln(6)
    _sig_w = W / 3
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*_BLK)
    for _sl in ["L'etudiant(e)", "Chef de departement", "Le Doyen"]:
        pdf.cell(_sig_w, 6, _sl, border=0, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*_G)
    for _ in range(3):
        pdf.cell(_sig_w, 6, "Signature & cachet", border=0, align="C")
    pdf.ln(12)
    _x0 = pdf.get_x()
    _y0 = pdf.get_y()
    for _i in range(3):
        pdf.line(_x0 + _sig_w * _i + 5, _y0, _x0 + _sig_w * (_i + 1) - 5, _y0)
    pdf.ln(8)

    # Pied de page
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*_G)
    pdf.cell(W, 5,
             f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} - UniSchedule",
             align="C")

    return bytes(pdf.output())


def generate_attendance_report_pdf(
    student_name: str,
    student_number: str,
    university_name: str,
    class_name: str,
    academic_year: str,
    attendance_stats: list,
) -> bytes:
    """Génère un rapport d'assiduité PDF pour un étudiant."""

    _DB  = (30, 64, 175)
    _B   = (37, 99, 235)
    _LB  = (239, 246, 255)
    _W   = (255, 255, 255)
    _G   = (100, 116, 139)
    _BRD = (203, 213, 225)
    _ALT = (248, 250, 252)
    _BLK = (15, 23, 42)
    _GRN = (5, 150, 105)
    _RED = (220, 38, 38)
    _AMB = (217, 119, 6)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    W = pdf.w - 30

    # En-tête
    pdf.set_fill_color(*_DB)
    pdf.set_text_color(*_W)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(W, 9, university_name.upper(), border=0, fill=True,
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_text_color(*_DB)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(W, 8, "RAPPORT D'ASSIDUITE", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_G)
    pdf.cell(W, 5, f"Annee academique : {academic_year or '-'}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Infos étudiant
    pdf.set_draw_color(*_BRD)
    pdf.set_text_color(*_BLK)
    for _lbl, _val in [("Nom et Prenom", student_name),
                       ("N Matricule", student_number),
                       ("Classe", class_name)]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*_LB)
        pdf.cell(40, 6, f"  {_lbl} :", border=1, fill=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(*_W)
        pdf.cell(W - 40, 6, f"  {_val or '-'}", border=1, fill=True,
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Résumé global
    if attendance_stats:
        _tp = sum(int(r.get("presences") or 0) for r in attendance_stats)
        _ta = sum(int(r.get("absences")  or 0) for r in attendance_stats)
        _ts = _tp + _ta
        _tg = round(_tp / _ts * 100, 1) if _ts else 0
        _gc = _GRN if _tg >= 75 else _AMB if _tg >= 50 else _RED
        _sw = W / 3
        pdf.set_fill_color(*_LB)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*_BLK)
        for _h in ["Seances assistees", "Absences", "Taux global"]:
            pdf.cell(_sw, 6, _h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_fill_color(*_W)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(_sw, 8, str(_tp), border=1, fill=True, align="C")
        pdf.cell(_sw, 8, str(_ta), border=1, fill=True, align="C")
        pdf.set_text_color(*_gc)
        pdf.cell(_sw, 8, f"{_tg}%", border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(*_BLK)
        pdf.ln(4)

    # Tableau par cours
    _CW2 = [90, 25, 25, 25, 25]
    pdf.set_fill_color(*_DB)
    pdf.set_text_color(*_W)
    pdf.set_font("Helvetica", "B", 8)
    for _h, _w in zip(["Cours", "Seances", "Presences", "Absences", "Taux %"], _CW2):
        pdf.cell(_w, 7, f" {_h}", border=1, fill=True, align="C")
    pdf.ln()

    _alt2 = False
    for _stat in (attendance_stats or []):
        _tx = float(_stat.get("taux_presence") or 0)
        _tc = _GRN if _tx >= 75 else _AMB if _tx >= 50 else _RED
        _bg = _ALT if _alt2 else _W
        pdf.set_fill_color(*_bg)
        pdf.set_text_color(*_BLK)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(_CW2[0], 6, f" {_stat.get('course_name','-')}", border=1, fill=True, align="L")
        pdf.cell(_CW2[1], 6, f" {_stat.get('total_seances','-')}", border=1, fill=True, align="C")
        pdf.cell(_CW2[2], 6, f" {_stat.get('presences','-')}", border=1, fill=True, align="C")
        pdf.cell(_CW2[3], 6, f" {_stat.get('absences','0')}", border=1, fill=True, align="C")
        pdf.set_text_color(*_tc)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(_CW2[4], 6, f" {_tx:.0f}%", border=1, fill=True, align="C")
        pdf.ln()
        _alt2 = not _alt2

    if not attendance_stats:
        pdf.set_fill_color(*_ALT)
        pdf.set_text_color(*_G)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(sum(_CW2), 6, "  Aucune donnee d'assiduite disponible.",
                 border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    # Pied de page
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*_G)
    pdf.cell(W, 5,
             f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} - UniSchedule",
             align="C")

    return bytes(pdf.output())
