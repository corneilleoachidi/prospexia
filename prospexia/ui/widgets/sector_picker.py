"""Sélecteur multi-secteurs : recherche, liste cochable groupée par catégorie, chips, secteur libre."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from prospexia.data.sectors import CATEGORIES, SECTOR_BY_KEY, SECTORS
from prospexia.ui import theme
from prospexia.ui.widgets.common import Chip, FlowLayout

CUSTOM_PREFIX = "custom:"


class SectorPicker(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected: dict[str, str] = {}  # key -> label

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Rechercher un secteur…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)

        self.list = QListWidget()
        self.list.setMinimumHeight(170)
        self.list.setMaximumHeight(230)
        self.list.itemChanged.connect(self._on_item_changed)
        self._build_list()
        lay.addWidget(self.list)

        row = QHBoxLayout()
        self.custom = QLineEdit()
        self.custom.setPlaceholderText("Secteur personnalisé (en français)…")
        self.custom.returnPressed.connect(self._add_custom)
        add = QPushButton("+")
        add.setFixedWidth(36)
        add.setToolTip("Ajouter ce secteur libre (traduit automatiquement)")
        add.clicked.connect(self._add_custom)
        row.addWidget(self.custom)
        row.addWidget(add)
        lay.addLayout(row)

        self.chips_host = QWidget()
        self.chips = FlowLayout(self.chips_host, spacing=6)
        lay.addWidget(self.chips_host)

        self.hint = QLabel("Aucun secteur sélectionné")
        self.hint.setObjectName("Hint")
        lay.addWidget(self.hint)

    # ------------------------------------------------------------------ construction
    def _build_list(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        for cat in CATEGORIES:
            header = QListWidgetItem(cat)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            f = QFont(); f.setBold(True); f.setPointSize(9)
            header.setFont(f)
            header.setForeground(QColor(theme.ACCENT_2))
            header.setData(Qt.ItemDataRole.UserRole, None)
            self.list.addItem(header)
            for s in SECTORS:
                if s.category != cat:
                    continue
                it = QListWidgetItem("    " + s.label_fr)
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
                it.setCheckState(Qt.CheckState.Checked if s.key in self._selected else Qt.CheckState.Unchecked)
                it.setData(Qt.ItemDataRole.UserRole, s.key)
                self.list.addItem(it)
        self.list.blockSignals(False)

    def _filter(self, text: str) -> None:
        t = text.strip().lower()
        for i in range(self.list.count()):
            it = self.list.item(i)
            key = it.data(Qt.ItemDataRole.UserRole)
            if key is None:
                it.setHidden(bool(t))  # masque les en-têtes pendant une recherche
            else:
                it.setHidden(bool(t) and t not in it.text().lower())

    # ------------------------------------------------------------------ interactions
    def _on_item_changed(self, it: QListWidgetItem) -> None:
        key = it.data(Qt.ItemDataRole.UserRole)
        if key is None:
            return
        if it.checkState() == Qt.CheckState.Checked:
            self._selected[key] = SECTOR_BY_KEY[key].label_fr
        else:
            self._selected.pop(key, None)
        self._refresh_chips()

    def _add_custom(self) -> None:
        text = self.custom.text().strip()
        if not text:
            return
        key = CUSTOM_PREFIX + text.lower()
        self._selected[key] = text
        self.custom.clear()
        self._refresh_chips()

    def _remove(self, key: str) -> None:
        self._selected.pop(key, None)
        if not key.startswith(CUSTOM_PREFIX):
            for i in range(self.list.count()):
                it = self.list.item(i)
                if it.data(Qt.ItemDataRole.UserRole) == key:
                    self.list.blockSignals(True)
                    it.setCheckState(Qt.CheckState.Unchecked)
                    self.list.blockSignals(False)
        self._refresh_chips()

    def _refresh_chips(self) -> None:
        self.chips.clear()
        for key, label in self._selected.items():
            chip = Chip(key, ("✎ " if key.startswith(CUSTOM_PREFIX) else "") + label)
            chip.removed.connect(self._remove)
            self.chips.addWidget(chip)
        n = len(self._selected)
        self.hint.setText("Aucun secteur sélectionné" if n == 0 else f"{n} secteur(s) sélectionné(s)")
        self.hint.setStyleSheet(f"color: {theme.MUTED if n == 0 else theme.ACCENT_2};")
        self.changed.emit()

    # ------------------------------------------------------------------ API
    def sector_keys(self) -> list[str]:
        return [k for k in self._selected if not k.startswith(CUSTOM_PREFIX)]

    def custom_sectors(self) -> list[str]:
        return [v for k, v in self._selected.items() if k.startswith(CUSTOM_PREFIX)]

    def labels(self) -> list[str]:
        return list(self._selected.values())

    def set_selection(self, keys: list[str]) -> None:
        self._selected = {k: SECTOR_BY_KEY[k].label_fr for k in keys if k in SECTOR_BY_KEY}
        self._build_list()
        self._refresh_chips()
