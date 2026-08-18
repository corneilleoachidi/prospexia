"""Petits widgets réutilisables : cartes de statistiques, chips, badges, layout fluide."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLayoutItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from prospexia.ui import theme


class FlowLayout(QLayout):
    """Layout qui passe à la ligne automatiquement (pour les chips)."""

    def __init__(self, parent: QWidget | None = None, margin: int = 0, spacing: int = 6):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, i: int) -> QLayoutItem | None:
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i: int) -> QLayoutItem | None:
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return self._do_layout(QRect(0, 0, w, 0), test=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for it in self._items:
            size = size.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do_layout(self, rect: QRect, test: bool) -> int:
        m = self.contentsMargins()
        x, y = rect.x() + m.left(), rect.y() + m.top()
        line_h = 0
        right = rect.right() - m.right()
        for it in self._items:
            w, h = it.sizeHint().width(), it.sizeHint().height()
            if x + w > right and line_h > 0:
                x = rect.x() + m.left()
                y += line_h + self.spacing()
                line_h = 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), it.sizeHint()))
            x += w + self.spacing()
            line_h = max(line_h, h)
        return y + line_h + m.bottom() - rect.y()

    def clear(self) -> None:
        while self._items:
            it = self._items.pop()
            if it.widget():
                it.widget().deleteLater()


class Chip(QFrame):
    removed = Signal(str)

    def __init__(self, key: str, text: str, removable: bool = True, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("Chip")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 4, 2)
        lay.setSpacing(4)
        lay.addWidget(QLabel(text))
        if removable:
            btn = QPushButton("✕")
            btn.setObjectName("ChipClose")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedWidth(18)
            btn.clicked.connect(lambda: self.removed.emit(self.key))
            lay.addWidget(btn)


class Badge(QLabel):
    def __init__(self, text: str = "", color: str = theme.MUTED, parent=None):
        super().__init__(text, parent)
        self.setObjectName("Badge")
        self.set_color(color)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_color(self, color: str) -> None:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        self.setStyleSheet(
            f"#Badge {{ background: rgba({r},{g},{b},0.14); color: {color}; "
            f"border: 1px solid rgba({r},{g},{b},0.35); }}")


class StatCard(QFrame):
    def __init__(self, label: str, color: str = theme.TEXT, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)
        self.value = QLabel("0")
        self.value.setObjectName("StatValue")
        self.value.setStyleSheet(f"color: {color};")
        lbl = QLabel(label.upper())
        lbl.setObjectName("StatLabel")
        lay.addWidget(self.value)
        lay.addWidget(lbl)

    def set(self, v: int | str) -> None:
        self.value.setText(str(v))


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("SectionLabel")
    return lbl
