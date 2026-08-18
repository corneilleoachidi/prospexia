"""Cache disque (SQLite) des requêtes fournisseurs et des analyses, avec expiration.

Objectif : ne pas reconsommer les quotas API (Google Places, SerpAPI) quand une recherche
identique — ou partiellement identique — est relancée dans le mois.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

from prospexia.config import APP_NAME
from prospexia.core.models import (
    Company,
    LegalInfo,
    Prospect,
    WebPresence,
    WebsiteCheck,
    WebsiteStatus,
)

CACHE_DIR = Path(user_cache_dir(APP_NAME))
CACHE_FILE = CACHE_DIR / "cache.sqlite3"
DAY = 86_400


class ResultCache:
    def __init__(self, path: Path = CACHE_FILE, ttl_days: int = 30):
        self.path = path
        self.ttl = ttl_days * DAY
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS queries (key TEXT PRIMARY KEY, ts REAL, data TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS analyses (key TEXT PRIMARY KEY, ts REAL, data TEXT)")
        self.conn.commit()

    # ------------------------------------------------------------------ bas niveau
    def _get(self, table: str, key: str) -> tuple[float, Any] | None:
        row = self.conn.execute(f"SELECT ts, data FROM {table} WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        ts, data = row
        if time.time() - ts > self.ttl:
            self.conn.execute(f"DELETE FROM {table} WHERE key = ?", (key,))
            self.conn.commit()
            return None
        return ts, json.loads(data)

    def _put(self, table: str, key: str, data: Any) -> None:
        self.conn.execute(f"INSERT OR REPLACE INTO {table} (key, ts, data) VALUES (?, ?, ?)",
                          (key, time.time(), json.dumps(data, ensure_ascii=False)))
        self.conn.commit()

    # ------------------------------------------------------------------ requêtes fournisseurs
    @staticmethod
    def query_key(provider: str, term: str, country: str, city: str | None, limit: int) -> str:
        return f"{provider}|{country}|{(city or '').lower()}|{term.lower().strip()}|{limit}"

    def get_query(self, key: str) -> list[Company] | None:
        hit = self._get("queries", key)
        if hit is None:
            return None
        return [Company(**c) for c in hit[1]]

    def put_query(self, key: str, companies: list[Company]) -> None:
        self._put("queries", key, [asdict(c) for c in companies])

    # ------------------------------------------------------------------ analyses
    @staticmethod
    def analysis_key(company: Company) -> str:
        return company.dedupe_key()

    def get_analysis(self, company: Company) -> tuple[float, WebsiteCheck, WebPresence, LegalInfo | None] | None:
        hit = self._get("analyses", self.analysis_key(company))
        if hit is None:
            return None
        ts, d = hit
        w = d["website"]
        w["status"] = WebsiteStatus(w["status"])
        website = WebsiteCheck(**w)
        presence = WebPresence(**d["presence"])
        legal = LegalInfo(**d["legal"]) if d.get("legal") else None
        return ts, website, presence, legal

    def put_analysis(self, p: Prospect) -> None:
        self._put("analyses", self.analysis_key(p.company), {
            "website": asdict(p.website),
            "presence": asdict(p.presence),
            "legal": asdict(p.legal) if p.legal else None,
            "company_website": p.company.website,
        })

    # ------------------------------------------------------------------ maintenance
    def stats(self) -> dict[str, int]:
        q = self.conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
        a = self.conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        return {"queries": q, "analyses": a}

    def purge_expired(self) -> None:
        limit = time.time() - self.ttl
        self.conn.execute("DELETE FROM queries WHERE ts < ?", (limit,))
        self.conn.execute("DELETE FROM analyses WHERE ts < ?", (limit,))
        self.conn.commit()

    def clear(self) -> None:
        self.conn.execute("DELETE FROM queries")
        self.conn.execute("DELETE FROM analyses")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
