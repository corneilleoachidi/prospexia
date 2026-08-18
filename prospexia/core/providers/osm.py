"""Fournisseur OpenStreetMap (Nominatim) — gratuit, sans clé, 1 requête/seconde max."""
from __future__ import annotations

import asyncio
import logging

from prospexia.core.models import Company
from prospexia.data.countries import Country

from .base import CompanyProvider

log = logging.getLogger(__name__)
_URL = "https://nominatim.openstreetmap.org/search"
_UA = "Prospexia/0.1 (prospection locale; contact: user)"
_lock = asyncio.Lock()
_BUSINESS_CLASSES = {"amenity", "shop", "craft", "office", "tourism", "leisure", "healthcare",
                     "club", "building", "man_made", "industrial", "landuse"}


class OSMProvider(CompanyProvider):
    name = "osm"

    async def search(self, term: str, country: Country, city: str | None, limit: int) -> list[Company]:
        q = f"{term} {city}" if city else term
        params = {
            "q": q,
            "format": "jsonv2",
            "countrycodes": country.code.lower(),
            "addressdetails": 1,
            "extratags": 1,
            "namedetails": 1,
            "limit": min(limit, 50),
            "accept-language": country.lang,
        }
        async with _lock:  # respect de la politique d'usage : 1 req/s
            resp = await self.client.get(_URL, params=params, headers={"User-Agent": _UA})
            await asyncio.sleep(1.1)
        if resp.status_code != 200:
            log.warning("Nominatim %s: %s", resp.status_code, resp.text[:120])
            return []
        out: list[Company] = []
        for item in resp.json():
            name = (item.get("namedetails") or {}).get("name") or item.get("name") or ""
            category = item.get("category") or item.get("class")
            if not name or category not in _BUSINESS_CLASSES:
                continue
            if name.strip().lower() == term.strip().lower():
                continue  # objet nommé d'après le type ("Plombier"), pas une vraie enseigne
            addr = item.get("address") or {}
            extra = item.get("extratags") or {}
            out.append(Company(
                name=name.strip(),
                address=item.get("display_name", ""),
                city=addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality", ""),
                phone=extra.get("phone") or extra.get("contact:phone", ""),
                website=extra.get("website") or extra.get("contact:website", ""),
                source="osm",
                lat=float(item["lat"]) if item.get("lat") else None,
                lon=float(item["lon"]) if item.get("lon") else None,
                source_id=str(item.get("osm_id", "")),
                maps_url=f"https://www.openstreetmap.org/{item.get('osm_type','node')}/{item.get('osm_id','')}",
            ))
        return out
