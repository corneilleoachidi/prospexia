"""Thème visuel de l'application (palette sombre + accents dégradés)."""
from __future__ import annotations

BG = "#0d0f16"
SURFACE = "#151824"
SURFACE_2 = "#1c2030"
BORDER = "#262b3d"
TEXT = "#e7e9f2"
MUTED = "#8b91a7"
ACCENT = "#7c5cff"
ACCENT_2 = "#3ec6ff"
SUCCESS = "#22c55e"
WARN = "#f59e0b"
DANGER = "#ef4444"

GRADIENT = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT}, stop:1 {ACCENT_2})"
GRADIENT_HOVER = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8f73ff, stop:1 #5dd2ff)"

QSS = f"""
* {{ font-family: "Inter", "Segoe UI", "SF Pro Display", "Ubuntu", "Noto Sans", sans-serif; }}
QMainWindow, QDialog {{ background: {BG}; }}
QWidget {{ color: {TEXT}; font-size: 13px; }}
QToolTip {{ background: {SURFACE_2}; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; border-radius: 6px; }}

#Sidebar {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #141827, stop:1 #0f1119);
  border-right: 1px solid {BORDER};
}}
#Brand {{ font-size: 26px; font-weight: 800; letter-spacing: 1px; color: {ACCENT_2}; }}
#BrandSub {{ color: {MUTED}; font-size: 12px; }}
#SectionLabel {{ color: {MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; margin-top: 6px; }}
#Card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
#StatCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
#StatValue {{ font-size: 26px; font-weight: 800; }}
#StatLabel {{ color: {MUTED}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
#PageTitle {{ font-size: 22px; font-weight: 800; }}
#PageSub {{ color: {MUTED}; }}
#StatusLabel {{ color: {MUTED}; }}
#Hint {{ color: {MUTED}; font-size: 11px; }}
#Chip {{ background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 12px; padding: 3px 8px; font-size: 12px; }}
#ChipClose {{ background: transparent; border: none; color: {MUTED}; font-weight: 700; padding: 0 2px; }}
#ChipClose:hover {{ color: {DANGER}; }}
#Badge {{ border-radius: 9px; padding: 2px 8px; font-size: 11px; font-weight: 700; }}

QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{
  background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 10px; padding: 8px 10px;
  selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid {MUTED}; margin-right: 8px; }}
QComboBox QAbstractItemView {{ background: {SURFACE_2}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; outline: none; padding: 4px; }}

QPushButton {{
  background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 10px; padding: 8px 14px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {ACCENT}; background: #222740; }}
QPushButton:pressed {{ background: #1a1e2e; }}
QPushButton:disabled {{ color: #5b6078; border-color: #1f2333; background: #161927; }}
QPushButton#Primary {{ background: {GRADIENT}; border: none; color: white; font-size: 14px; padding: 12px 18px; border-radius: 12px; }}
QPushButton#Primary:hover {{ background: {GRADIENT_HOVER}; }}
QPushButton#Primary:disabled {{ background: #2a2f45; color: #6b7190; }}
QPushButton#Danger {{ background: transparent; border: 1px solid {DANGER}; color: {DANGER}; }}
QPushButton#Danger:hover {{ background: rgba(239,68,68,0.12); }}
QPushButton#Ghost {{ background: transparent; border: 1px solid transparent; color: {MUTED}; }}
QPushButton#Ghost:hover {{ color: {TEXT}; border-color: {BORDER}; }}
QPushButton#Pill {{ background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 14px; padding: 5px 4px; min-width: 22px; }}
QPushButton#Pill:checked {{ background: {GRADIENT}; border: none; color: white; }}
QPushButton#Segment {{ background: {SURFACE_2}; border: 1px solid {BORDER}; padding: 8px 12px; border-radius: 10px; }}
QPushButton#Segment:checked {{ background: {GRADIENT}; border: none; color: white; }}
QPushButton#Icon {{ background: transparent; border: none; padding: 4px; font-size: 16px; }}
QPushButton#Icon:hover {{ background: {SURFACE_2}; border-radius: 8px; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1px solid {BORDER}; background: {SURFACE_2}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: none; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}

QListWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; outline: none; color: {TEXT}; padding: 4px; }}
QListWidget::indicator {{ width: 15px; height: 15px; border-radius: 4px; border: 1px solid {BORDER}; background: {SURFACE_2}; }}
QListWidget::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QListWidget::item:disabled {{ color: {MUTED}; }}
QListWidget::item {{ padding: 6px 8px; border-radius: 8px; }}
QListWidget::item:hover {{ background: {SURFACE_2}; }}
QListWidget::item:selected {{ background: rgba(124,92,255,0.25); color: {TEXT}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #384060; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}

QTableView {{
  background: {SURFACE}; alternate-background-color: #181c29; border: 1px solid {BORDER}; border-radius: 12px;
  gridline-color: transparent; selection-background-color: rgba(124,92,255,0.22); selection-color: {TEXT};
}}
QTableView::item {{ padding: 6px 8px; border-bottom: 1px solid #1d2131; }}
QHeaderView::section {{
  background: {SURFACE_2}; color: {MUTED}; padding: 9px 8px; border: none; border-bottom: 1px solid {BORDER};
  font-weight: 700; font-size: 11px; letter-spacing: 0.8px;
}}
QTableCornerButton::section {{ background: {SURFACE_2}; border: none; }}

QProgressBar {{ background: {SURFACE_2}; border: none; border-radius: 4px; height: 8px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {GRADIENT}; border-radius: 4px; }}

QSplitter::handle {{ background: {BORDER}; width: 1px; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; }}
QTabBar::tab {{ background: transparent; padding: 8px 14px; color: {MUTED}; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QMenu {{ background: {SURFACE_2}; border: 1px solid {BORDER}; padding: 6px; border-radius: 8px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT}; }}
QMessageBox {{ background: {SURFACE}; }}
QLabel#Link {{ color: {ACCENT_2}; }}
"""

VERDICT_COLORS = {"priority": SUCCESS, "target": WARN, "out": "#6b7190"}
STATUS_COLORS = {"none": DANGER, "dead": DANGER, "social": WARN, "platform": WARN, "obsolete": WARN, "ok": SUCCESS}
