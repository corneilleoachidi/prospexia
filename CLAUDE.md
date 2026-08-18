# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Prospexia is a French-language desktop app (Python 3.11+, PySide6) that finds businesses in a
country × set of sectors and scores their online presence to identify prospects for website creation
/ SEO services. UI strings, comments and docs are in French; keep it that way.

## Commands

Tooling is `uv` (installed at `~/.local/bin/uv`; the venv is `.venv/`). No system pip is available.

```bash
uv sync --extra dev                  # install deps
uv run prospexia                     # launch the GUI (python -m prospexia also works)
uv run pytest -q                     # all tests (Qt runs offscreen via tests/conftest.py)
uv run pytest tests/test_presence.py::test_old_site_obsolete -q   # single test
uv run ruff check --fix prospexia    # lint (rules in pyproject: E,F,I,UP,B; E701/E702 allowed)
```

Headless screenshot for UI checks: `QT_QPA_PLATFORM=offscreen uv run python -c '...MainWindow(...).grab().save(...)'`.

## Architecture

Data flow: `SearchRequest` → `core/pipeline.py:Pipeline.run()` (asyncio, one shared `httpx.AsyncClient`) →
1. **translate** sector keys to the country language (`core/translate.py`: `data/sectors.py` catalog first,
   `deep-translator` fallback with a JSON cache in the user config dir);
2. **search** companies per (term × location) — locations = country-wide then each city from
   `data/countries.py`; providers in `core/providers/` (`GooglePlacesProvider` if a key is set,
   `OSMProvider` as fallback — a `ProviderError` from Google drops it and continues with OSM);
   dedupe with `Company.dedupe_key()`;
3. **analyze** each company concurrently (semaphore = `Settings.concurrency`): `core/presence.py`
   `check_website()` first (HTTP fetch → `WebsiteStatus` NONE/DEAD/OBSOLETE/SOCIAL_ONLY/THIRD_PARTY/OK
   with issue list; THIRD_PARTY = Planity/PagesJaunes/WhatsApp… fiche, i.e. no own site). If the site is
   OK the prospect is OUT regardless, so the web search is **skipped** (`WebPresence.skipped`) to save
   SerpAPI quota; otherwise `web_presence()` runs (SerpAPI or DuckDuckGo) and may discover a website the
   provider didn't list, which is then checked too;
   Before any network call, `core/cache.py:ResultCache` (SQLite in the user cache dir, TTL
   `Settings.cache_ttl_days`) is consulted: provider queries are cached by (provider, term, country, city,
   limit) and analyses by `Company.dedupe_key()`; scoring is always recomputed so cached analyses work
   across modes.
4. **score** in `core/scoring.py` (`score_prospect`: 0 = invisible … 100 = very present; verdict depends
   on `RelevanceMode` STRICT/FLEXIBLE) — the pipeline stops once `max_results` non-OUT prospects are found.
   All analysed prospects (including OUT) are emitted via `on_prospect`; only non-OUT are returned.
5. **legal enrichment** for non-OUT prospects only (`core/registry/`): `registry_for(country)` →
   `FranceRegistry` (free public API, name+postal-code matching, threshold 0.55) or `LinkOnlyRegistry`
   (prefilled search URL). Result is `Prospect.legal: LegalInfo` and is cached with the analysis.

UI (`prospexia/ui/`): `main_window.py` = sidebar form + results area; `worker.py` runs the pipeline in a
`QThread` with its own asyncio loop and forwards progress/prospect signals; `widgets/` holds the
multi-select `SectorPicker`, the `ResultsTable` (model + proxy filter + score/verdict delegates), and
dialogs. All styling is QSS in `ui/theme.py` — note Qt QSS uses `#AARRGGBB`, so alpha colours must be
written as `rgba(...)` (see `Badge.set_color`).

Persistent settings/API keys: `config.py:Settings` (JSON via platformdirs). Export: `core/export.py`
(CSV/XLSX via openpyxl; PDF via `QTextDocument` → `QPdfWriter`, so it needs a `QGuiApplication` — the
HTML is a limited Qt subset: `bgcolor`, `cellpadding`, inline `style` only, no CSS classes).

## Gotchas

- **Do not run the real pipeline against Google/SerpAPI for testing** — the user's SerpAPI free plan is
  250 searches/month and was already largely consumed by tests. Use mocked `httpx.MockTransport` tests.
  The French registry API is free and keyless, a single sanity call is acceptable.
- DuckDuckGo HTML returns HTTP 202 anti-bot challenges after a few queries; `presence.py` serialises
  DDG calls and raises `SearchUnavailable`, which leaves `WebPresence.search_engine == ""` and is scored as
  "not assessed" rather than "invisible". SerpAPI is the intended primary engine.
- Nominatim usage policy: 1 request/second (enforced by a lock in `OSMProvider`) and a User-Agent.
- Google Places Text Search returns max 60 results per query (3 pages) — that's why queries fan out per city.
