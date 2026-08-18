"""Tableau des prospects : modèle Qt + délégués (score en barre, verdict en badge)."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRect, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHeaderView, QStyledItemDelegate, QTableView

from prospexia.core.models import Prospect, Verdict
from prospexia.ui import theme

COLS = ["Entreprise", "Secteur", "Ville", "Téléphone", "Site web", "État du site", "Score", "Verdict", "Opportunité", "Identifiant"]
COL_SCORE, COL_VERDICT, COL_STATUS = 6, 7, 5

VERDICT_HELP = {
    Verdict.PRIORITY: ("Cible idéale : pas de site web propre (aucun site, page Facebook seule, fiche "
                       "Planity/PagesJaunes ou site hors service) ET présence en ligne quasi nulle. "
                       "À contacter en premier."),
    Verdict.TARGET: ("Bon prospect : site absent, obsolète ou HS, mais déjà un peu de présence en ligne "
                     "(réseaux sociaux, avis, résultats web)."),
    Verdict.OUT: ("Pas un prospect : site fonctionnel et moderne, ou présence en ligne déjà solide. "
                  "Masqué par défaut (case « Afficher les hors cible »)."),
}
HEADER_HELP = {
    COL_STATUS: ("État du site déclaré :\n• Aucun site\n• Réseau social seul (page Facebook/Instagram)\n"
                 "• Plateforme tierce seule (fiche Planity, PagesJaunes, WhatsApp…)\n"
                 "• Site HS (injoignable, erreur)\n• Site obsolète (pas de HTTPS, non mobile, vieux copyright…)\n"
                 "• Site OK (fonctionnel et moderne)"),
    COL_SCORE: ("Score de présence en ligne, de 0 (invisible) à 100 (très présent).\n"
                "Additionne : état du site, réseaux sociaux trouvés, résultats web sur le nom, "
                "annuaires, avis Google.\nVert ≤ 25 · Orange ≤ 50 · Rouge au-delà."),
    COL_VERDICT: ("Conclusion de l'analyse :\n🟢 Prioritaire — pas de site propre + quasi invisible en ligne\n"
                  "🟡 Cible — site absent/obsolète/HS + présence faible\n"
                  "⚪ Hors cible — site OK ou présence déjà solide\n\n"
                  "Les seuils dépendent du mode (Strict / Flexible). Survolez une cellule pour le détail."),
    8: "Prestation à proposer, déduite de l'état du site : création, refonte + SEO, ou SEO seul.",
}


class ProspectModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.rows: list[Prospect] = []

    def clear(self) -> None:
        self.beginResetModel(); self.rows.clear(); self.endResetModel()

    def add(self, p: Prospect) -> None:
        n = len(self.rows)
        self.beginInsertRows(QModelIndex(), n, n)
        self.rows.append(p)
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(COLS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        p = self.rows[index.row()]
        c = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                p.company.name, p.company.sector, p.company.city, p.company.phone,
                p.company.website or "—", p.website.status.label, p.score, p.verdict.label, p.opportunity,
                (p.legal.identifier if p.legal and p.legal.identifier else "—"),
            ][c]
        if role == Qt.ItemDataRole.UserRole:
            return p
        if role == Qt.ItemDataRole.ToolTipRole:
            if c == COL_VERDICT:
                return (f"<b>{p.verdict.label}</b> — {VERDICT_HELP[p.verdict]}<br><br>"
                        f"<b>Pourquoi :</b><br>• " + "<br>• ".join(p.reasons))
            if c == COL_SCORE:
                return f"<b>Score {p.score}/100</b><br>• " + "<br>• ".join(p.reasons)
            return " · ".join(p.reasons)
        if role == Qt.ItemDataRole.ForegroundRole:
            if c == COL_STATUS:
                return QColor(theme.STATUS_COLORS[p.website.status.value])
            if c == 4 and not p.company.website:
                return QColor(theme.MUTED)
        if role == Qt.ItemDataRole.FontRole and c == 0:
            f = QFont(); f.setBold(True); return f
        return None


class ProspectProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.show_out = False
        self.text = ""
        self.setSortRole(Qt.ItemDataRole.DisplayRole)

    def set_show_out(self, v: bool) -> None:
        self.show_out = v; self.invalidateRowsFilter()

    def set_text(self, t: str) -> None:
        self.text = t.lower().strip(); self.invalidateRowsFilter()

    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        p: Prospect = self.sourceModel().rows[row]
        if not self.show_out and p.verdict is Verdict.OUT:
            return False
        if self.text:
            hay = f"{p.company.name} {p.company.city} {p.company.sector} {p.company.address}".lower()
            return self.text in hay
        return True


class ScoreDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        score = int(index.data(Qt.ItemDataRole.DisplayRole) or 0)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r: QRect = option.rect.adjusted(10, 0, -10, 0)
        bar = QRect(r.left(), r.center().y() - 3, r.width() - 34, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.SURFACE_2))
        painter.drawRoundedRect(bar, 3, 3)
        color = theme.SUCCESS if score <= 25 else theme.WARN if score <= 50 else theme.DANGER
        fill = QRect(bar.left(), bar.top(), int(bar.width() * score / 100), bar.height())
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(fill, 3, 3)
        painter.setPen(QPen(QColor(theme.TEXT)))
        painter.drawText(QRect(bar.right() + 6, r.top(), 28, r.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, str(score))
        painter.restore()


class VerdictDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        p: Prospect = index.data(Qt.ItemDataRole.UserRole)
        color = QColor(theme.VERDICT_COLORS[p.verdict.value])
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = option.fontMetrics
        text = p.verdict.label
        w = fm.horizontalAdvance(text) + 18
        r = QRect(option.rect.left() + 8, option.rect.center().y() - 10, w, 20)
        bg = QColor(color); bg.setAlpha(40)
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 110)))
        painter.setBrush(bg)
        painter.drawRoundedRect(r, 10, 10)
        painter.setPen(QPen(color))
        f = painter.font(); f.setBold(True); painter.setFont(f)
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class ResultsTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_ = ProspectModel()
        self.proxy = ProspectProxy()
        self.proxy.setSourceModel(self.model_)
        self.setModel(self.proxy)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(38)
        self.setItemDelegateForColumn(COL_SCORE, ScoreDelegate(self))
        self.setItemDelegateForColumn(COL_VERDICT, VerdictDelegate(self))
        h = self.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setStretchLastSection(True)
        h.setHighlightSections(False)
        for i, w in enumerate([200, 125, 100, 120, 160, 110, 105, 95, 140, 110]):
            self.setColumnWidth(i, w)
        self.sortByColumn(COL_SCORE, Qt.SortOrder.AscendingOrder)

    def prospect_at(self, proxy_index: QModelIndex) -> Prospect | None:
        if not proxy_index.isValid():
            return None
        return self.proxy.data(proxy_index, Qt.ItemDataRole.UserRole)

    def visible_prospects(self) -> list[Prospect]:
        return [self.proxy.data(self.proxy.index(r, 0), Qt.ItemDataRole.UserRole)
                for r in range(self.proxy.rowCount())]
