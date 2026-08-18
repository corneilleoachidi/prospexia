"""Export des prospects en CSV / Excel."""
from __future__ import annotations

import csv
from pathlib import Path

from prospexia.core.models import Prospect

COLUMNS = [
    ("Entreprise", lambda p: p.company.name),
    ("Secteur", lambda p: p.company.sector),
    ("Ville", lambda p: p.company.city),
    ("Adresse", lambda p: p.company.address),
    ("Téléphone", lambda p: p.company.phone),
    ("Site web", lambda p: p.company.website),
    ("État du site", lambda p: p.website.status.label),
    ("Score présence", lambda p: p.score),
    ("Verdict", lambda p: p.verdict.label),
    ("Opportunité", lambda p: p.opportunity),
    ("Réseaux sociaux", lambda p: ", ".join(p.presence.socials.values())),
    ("Résultats web", lambda p: p.presence.search_hits),
    ("Avis Google", lambda p: p.company.reviews_count),
    ("Note Google", lambda p: p.company.rating if p.company.rating is not None else ""),
    ("Diagnostic", lambda p: " · ".join(p.reasons)),
    ("Source", lambda p: p.company.source),
    ("Lien carte", lambda p: p.company.maps_url),
]


def export_csv(prospects: list[Prospect], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([c for c, _ in COLUMNS])
        for p in prospects:
            w.writerow([fn(p) for _, fn in COLUMNS])
    return path


def export_xlsx(prospects: list[Prospect], path: Path) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Prospects"
    ws.append([c for c, _ in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="5B4BDB")
        cell.alignment = Alignment(vertical="center")
    fills = {"Prioritaire": "DCFCE7", "Cible": "FEF9C3", "Hors cible": "FEE2E2"}
    for p in prospects:
        ws.append([fn(p) for _, fn in COLUMNS])
        row = ws.max_row
        color = fills.get(p.verdict.label)
        if color:
            ws.cell(row=row, column=9).fill = PatternFill("solid", fgColor=color)
    for i in range(1, len(COLUMNS) + 1):
        width = max(12, min(50, max(len(str(ws.cell(row=r, column=i).value or ""))
                                    for r in range(1, ws.max_row + 1)) + 2))
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(path)
    return path
