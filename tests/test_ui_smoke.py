"""Le fenêtre principale se construit et réagit sans planter (rendu offscreen)."""
import pytest
from PySide6.QtWidgets import QApplication

from prospexia.config import Settings
from prospexia.core.models import (
    Company,
    Prospect,
    RelevanceMode,
    Verdict,
    WebsiteCheck,
    WebsiteStatus,
)
from prospexia.core.scoring import score_prospect


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_main_window_builds_and_accepts_prospects(app, tmp_path):
    from prospexia.ui.main_window import MainWindow
    s = Settings(export_dir=str(tmp_path))
    w = MainWindow(s)
    assert not w.launch.isEnabled()
    w.sectors.set_selection(["plombier", "coiffeur"])
    assert w.launch.isEnabled()
    assert w.sectors.sector_keys() == ["plombier", "coiffeur"]

    p = Prospect(company=Company(name="Chez Marcel", city="Lyon", sector="Plombier"))
    p.website = WebsiteCheck(status=WebsiteStatus.NONE)
    score_prospect(p, RelevanceMode.STRICT)
    w._on_prospect(p)
    assert w.table.model_.rowCount() == 1
    assert w.card_found.value.text() == "1"
    assert p.verdict is Verdict.PRIORITY
    w.table.proxy.set_text("marcel")
    assert w.table.proxy.rowCount() == 1
    w.table.proxy.set_text("zzz")
    assert w.table.proxy.rowCount() == 0
