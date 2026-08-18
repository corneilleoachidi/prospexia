from pathlib import Path

from prospexia.core.export import export_csv, export_xlsx
from prospexia.core.models import Company, Prospect, WebsiteCheck, WebsiteStatus
from prospexia.core.translate import sector_term
from prospexia.data.countries import COUNTRIES, COUNTRY_BY_CODE
from prospexia.data.sectors import SECTOR_BY_KEY, SECTORS


def test_sectors_have_all_core_translations():
    for s in SECTORS:
        for lang in ("en", "de", "es", "it", "pt", "nl"):
            assert s.translations.get(lang), f"{s.key} manque {lang}"
    assert len(SECTOR_BY_KEY) == len(SECTORS)


def test_countries_unique_and_have_cities():
    assert len({c.code for c in COUNTRIES}) == len(COUNTRIES)
    assert COUNTRY_BY_CODE["FR"].cities
    assert COUNTRY_BY_CODE["DE"].lang == "de"


def test_sector_term_uses_catalog_without_network():
    assert sector_term("plombier", "fr") == "Plombier"
    assert sector_term("plombier", "de") == "Klempner"


def test_dedupe_key_ignores_case_and_punctuation():
    a = Company(name="Chez Marcel", city="Lyon")
    b = Company(name="chez-marcel !", city="LYON")
    assert a.dedupe_key() == b.dedupe_key()


def test_exports(tmp_path: Path):
    p = Prospect(company=Company(name="Chez Marcel", city="Lyon", sector="Restaurant"))
    p.website = WebsiteCheck(status=WebsiteStatus.NONE)
    p.reasons = ["Aucun site"]
    csv_path = export_csv([p], tmp_path / "out" / "x.csv")
    assert csv_path.exists()
    assert "Chez Marcel" in csv_path.read_text(encoding="utf-8-sig")
    xlsx_path = export_xlsx([p], tmp_path / "x.xlsx")
    assert xlsx_path.stat().st_size > 0


def test_pdf_export(tmp_path: Path):
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from prospexia.core.export import build_pdf_html, export_pdf
    from prospexia.core.models import LegalInfo
    p = Prospect(company=Company(name="Chez Marcel <b>", city="Lyon", sector="Restaurant", phone="04 00"))
    p.website = WebsiteCheck(status=WebsiteStatus.NONE)
    p.legal = LegalInfo(registry="Recherche d'entreprises", identifier="123456789", identifier_label="SIREN",
                        legal_form="SARL", managers=["Marcel DUPONT (Gérant)"], matched=True, vat_number="FR00123456789")
    html = build_pdf_html([p], "France — Restaurant", "Mode Strict")
    assert "Chez Marcel &lt;b&gt;" in html and "SIREN" in html and "Marcel DUPONT" in html
    out = export_pdf([p], tmp_path / "r.pdf", "France — Restaurant", "Mode Strict")
    assert out.exists() and out.read_bytes()[:5] == b"%PDF-"


def test_legal_columns_in_csv(tmp_path: Path):
    from prospexia.core.models import LegalInfo
    p = Prospect(company=Company(name="X"))
    p.legal = LegalInfo(identifier="123456789", identifier_label="SIREN", matched=True)
    txt = export_csv([p], tmp_path / "x.csv").read_text(encoding="utf-8-sig")
    assert "SIREN 123456789" in txt and "auto" in txt
