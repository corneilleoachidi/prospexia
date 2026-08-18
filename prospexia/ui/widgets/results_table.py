"""Tableau des prospects : modèle Qt + délégués (score en barre, verdict en badge)."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRect, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHeaderView, QStyledItemDelegate, QTableView

from prospexia.core.models import Prospect, Verdict
from prospexia.ui import theme

COLS = ["Entreprise", "Secteur", "Ville", "Téléphone", "Site web", "État du site", "Score", "Verdict", "Opportunité"]
COL_SCORE, COL_VERDICT, COL_STATUS = 6, 7, 5


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
            ][c]
        if role == Qt.ItemDataRole.UserRole:
            return p
        if role == Qt.ItemDataRole.ToolTipRole:
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
        for i, w in enumerate([200, 130, 100, 125, 170, 110, 110, 100, 150]):
            self.setColumnWidth(i, w)
        self.sortByColumn(COL_SCORE, Qt.SortOrder.AscendingOrder)

    def prospect_at(self, proxy_index: QModelIndex) -> Prospect | None:
        if not proxy_index.isValid():
            return None
        return self.proxy.data(proxy_index, Qt.ItemDataRole.UserRole)

    def visible_prospects(self) -> list[Prospect]:
        return [self.proxy.data(self.proxy.index(r, 0), Qt.ItemDataRole.UserRole)
                for r in range(self.proxy.rowCount())]
