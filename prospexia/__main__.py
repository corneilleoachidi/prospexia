"""Point d'entrée : `python -m prospexia` ou la commande `prospexia`."""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    from PySide6.QtGui import QColor, QFont, QPalette
    from PySide6.QtWidgets import QApplication

    from prospexia.config import Settings
    from prospexia.ui import theme
    from prospexia.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Prospexia")
    app.setDesktopFileName("prospexia")
    icon_path = Path(__file__).resolve().parent.parent / "assets" / "prospexia.svg"
    if icon_path.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyle("Fusion")
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, QColor(theme.BG))
    pal.setColor(QPalette.ColorRole.Base, QColor(theme.SURFACE_2))
    pal.setColor(QPalette.ColorRole.Text, QColor(theme.TEXT))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(theme.TEXT))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(theme.TEXT))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(theme.ACCENT))
    app.setPalette(pal)
    f = QFont(); f.setPointSize(10); app.setFont(f)
    app.setStyleSheet(theme.QSS)

    win = MainWindow(Settings.load())
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
