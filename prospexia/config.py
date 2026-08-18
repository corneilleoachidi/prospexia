"""Configuration persistante (clés API, préférences) stockée dans le dossier utilisateur."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from platformdirs import user_config_dir, user_documents_dir

APP_NAME = "Prospexia"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Settings:
    google_places_api_key: str = ""
    serpapi_api_key: str = ""
    export_dir: str = field(default_factory=lambda: str(Path(user_documents_dir()) / APP_NAME))
    concurrency: int = 8           # nombre de vérifications web simultanées
    request_timeout: float = 12.0  # secondes
    use_cache: bool = True         # réutiliser les résultats récents (économie de quotas API)
    cache_ttl_days: int = 30
    enrich_legal: bool = True      # interroger le registre officiel pour les prospects retenus
    last_country: str = "FR"
    last_sectors: list[str] = field(default_factory=list)
    last_max_results: int = 20
    last_mode: str = "strict"

    # ------------------------------------------------------------------ helpers
    @property
    def has_google(self) -> bool:
        return bool(self.google_places_api_key.strip())

    @property
    def has_serpapi(self) -> bool:
        return bool(self.serpapi_api_key.strip())

    @classmethod
    def load(cls) -> Settings:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
                return cls(**known)
            except (OSError, ValueError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
