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
