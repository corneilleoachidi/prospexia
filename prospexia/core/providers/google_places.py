"""Fournisseur Google Places API (New) — Text Search."""
from __future__ import annotations

import asyncio
import logging

import httpx

from prospexia.core.models import Company
from prospexia.data.countries import Country

from .base import CompanyProvider, ProviderError

log = logging.getLogger(__name__)

_URL = "https://places.googleapis.com/v1/places:searchText"
_FIELDS = ",".join([
    "nextPageToken",
    "places.id", "places.displayName", "places.formattedAddress", "places.addressComponents",
    "places.nationalPhoneNumber", "places.internationalPhoneNumber", "places.websiteUri",
    "places.rating", "places.userRatingCount", "places.location", "places.googleMapsUri",
    "places.businessStatus",
])


class GooglePlacesProvider(CompanyProvider):
    name = "google"

    def __init__(self, client: httpx.AsyncClient, api_key: str):
        super().__init__(client)
        self.api_key = api_key

    async def search(self, term: str, country: Country, city: str | None, limit: int) -> list[Company]:
        query = f"{term} {city}" if city else f"{term} {country.name_fr}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": _FIELDS,
        }
        results: list[Company] = []
        page_token: str | None = None
        for _ in range(3):  # Google limite à 3 pages (60 résultats) par requête
            body: dict = {
                "textQuery": query,
                "regionCode": country.code,
                "languageCode": country.lang,
                "pageSize": 20,
            }
            if page_token:
                body["pageToken"] = page_token
            resp = await self.client.post(_URL, json=body, headers=headers)
            if resp.status_code in (400, 401, 403):
                detail = resp.json().get("error", {}).get("message", resp.text[:200])
                raise ProviderError(f"Google Places : {detail}")
            if resp.status_code == 429:
                await asyncio.sleep(2)
                continue
            resp.raise_for_status()
            data = resp.json()
            for p in data.get("places", []):
                if p.get("businessStatus") == "CLOSED_PERMANENTLY":
                    continue
                results.append(_to_company(p))
            page_token = data.get("nextPageToken")
            if not page_token or len(results) >= limit:
                break
            await asyncio.sleep(0.3)
        return results[:limit]


def _to_company(p: dict) -> Company:
    city = ""
    for comp in p.get("addressComponents", []):
        types = comp.get("types", [])
        if "locality" in types or "postal_town" in types:
            city = comp.get("longText", "")
            break
    loc = p.get("location", {})
    return Company(
        name=p.get("displayName", {}).get("text", "").strip(),
        address=p.get("formattedAddress", ""),
        city=city,
        phone=p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber", ""),
        website=p.get("websiteUri", "") or "",
        source="google",
        rating=p.get("rating"),
        reviews_count=int(p.get("userRatingCount", 0) or 0),
        lat=loc.get("latitude"),
        lon=loc.get("longitude"),
        source_id=p.get("id", ""),
        maps_url=p.get("googleMapsUri", ""),
    )
