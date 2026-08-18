"""Traduction des secteurs d'activité vers la langue du pays ciblé.

1. Catalogue prétraduit (data/sectors.py) — instantané et fiable.
2. Sinon, deep-translator (Google Translate) avec cache disque.
"""
from __future__ import annotations

import json
import logging

from prospexia.config import CONFIG_DIR
from prospexia.data.sectors import SECTOR_BY_KEY

log = logging.getLogger(__name__)
_CACHE_FILE = CONFIG_DIR / "translations.json"
_cache: dict[str, str] | None = None


def _load_cache() -> dict[str, str]:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _save_cache() -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(_load_cache(), ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def translate_text(text_fr: str, lang: str) -> str:
    """Traduit un texte FR vers `lang`. Retourne le texte d'origine en cas d'échec."""
    if lang == "fr" or not text_fr.strip():
        return text_fr
    cache = _load_cache()
    key = f"{lang}:{text_fr.strip().lower()}"
    if key in cache:
        return cache[key]
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="fr", target=lang).translate(text_fr)
        if translated:
            cache[key] = translated
            _save_cache()
            return translated
    except Exception as exc:  # réseau, quota, langue non supportée…
        log.warning("Traduction impossible (%s -> %s): %s", text_fr, lang, exc)
    return text_fr


def sector_term(sector_key: str, lang: str) -> str:
    """Terme de recherche localisé pour un secteur du catalogue."""
    sector = SECTOR_BY_KEY[sector_key]
    term = sector.term(lang)
    if term:
        return term
    return translate_text(sector.label_fr, lang)
