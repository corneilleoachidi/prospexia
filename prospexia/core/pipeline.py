"""Orchestration : traduction -> recherche d'entreprises -> analyse de présence -> scoring."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

import httpx

from prospexia.config import Settings
from prospexia.core.models import (
    Company,
    ProgressEvent,
    Prospect,
    SearchRequest,
    Verdict,
    WebPresence,
    WebsiteStatus,
)
from prospexia.core.presence import check_website, web_presence
from prospexia.core.providers import (
    CompanyProvider,
    GooglePlacesProvider,
    OSMProvider,
    ProviderError,
)
from prospexia.core.scoring import score_prospect
from prospexia.core.translate import sector_term, translate_text
from prospexia.data.countries import COUNTRY_BY_CODE
from prospexia.data.sectors import SECTOR_BY_KEY

log = logging.getLogger(__name__)

ProgressCb = Callable[[ProgressEvent], None]
ProspectCb = Callable[[Prospect], None]


class PipelineCancelled(Exception):
    pass


class Pipeline:
    def __init__(self, settings: Settings, on_progress: ProgressCb | None = None,
                 on_prospect: ProspectCb | None = None):
        self.settings = settings
        self.on_progress = on_progress or (lambda e: None)
        self.on_prospect = on_prospect or (lambda p: None)
        self.cancel_event = asyncio.Event()
        self.warnings: list[str] = []
        self.analyzed = 0

    def cancel(self) -> None:
        self.cancel_event.set()

    def _check_cancel(self) -> None:
        if self.cancel_event.is_set():
            raise PipelineCancelled()

    # ------------------------------------------------------------------ run
    async def run(self, req: SearchRequest) -> list[Prospect]:
        country = COUNTRY_BY_CODE[req.country_code]
        timeout = httpx.Timeout(self.settings.request_timeout)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # 1) traduction des secteurs
            self.on_progress(ProgressEvent("translate", f"Traduction des secteurs ({country.lang})…"))
            terms: list[tuple[str, str]] = []  # (label_fr, terme localisé)
            for key in req.sector_keys:
                label = SECTOR_BY_KEY[key].label_fr
                term = await asyncio.to_thread(sector_term, key, country.lang)
                terms.append((label, term))
            for custom in req.custom_sectors:
                term = await asyncio.to_thread(translate_text, custom, country.lang)
                terms.append((custom, term))
            self._check_cancel()
            if not terms:
                return []
            self.on_progress(ProgressEvent(
                "translate", "Termes : " + ", ".join(f"{fr} → {t}" for fr, t in terms)))

            # 2) fournisseur
            providers: list[CompanyProvider] = []
            if self.settings.has_google:
                providers.append(GooglePlacesProvider(client, self.settings.google_places_api_key))
            providers.append(OSMProvider(client))

            # 3) plan de requêtes : pays entier d'abord, puis ville par ville
            locations: list[str | None] = [None, *country.cities]
            plan = [(label, term, loc) for loc in locations for (label, term) in terms]

            seen: set[str] = set()
            results: list[Prospect] = []
            sem = asyncio.Semaphore(self.settings.concurrency)
            found = 0
            batch_size = max(1, len(terms))  # une "tournée" = tous les secteurs pour une localité

            for i in range(0, len(plan), batch_size):
                self._check_cancel()
                if found >= req.max_results:
                    break
                batch = plan[i:i + batch_size]
                loc_label = batch[0][2] or country.name_fr
                self.on_progress(ProgressEvent(
                    "search", f"Recherche d'entreprises — {loc_label}",
                    current=i, total=len(plan), found=found))

                companies: list[Company] = []
                for label, term, loc in batch:
                    per_query = min(60, max(20, (req.max_results - found) * 2))
                    comps = await self._search(providers, term, country, loc, per_query)
                    for c in comps:
                        c.sector = label
                        k = c.dedupe_key()
                        if k in seen or not c.name:
                            continue
                        seen.add(k)
                        companies.append(c)
                if not companies:
                    continue

                # 4) analyse concurrente
                async def analyze(c: Company) -> Prospect:
                    async with sem:
                        self._check_cancel()
                        p = Prospect(company=c)
                        p.website = await check_website(client, c.website)
                        if p.website.status is WebsiteStatus.OK:
                            # Site fonctionnel => hors cible quoi qu'il arrive : on économise
                            # une recherche web (quota SerpAPI) et on passe au suivant.
                            p.presence = WebPresence(skipped=True)
                        else:
                            p.presence = await web_presence(client, c, country,
                                                            self.settings.serpapi_api_key)
                            if not c.website and p.presence.discovered_website:
                                c.website = p.presence.discovered_website
                                p.presence.own_domain_in_results = True
                                p.website = await check_website(client, c.website)
                                p.website.issues.insert(0, "Site trouvé via la recherche web")
                        score_prospect(p, req.mode)
                        return p

                tasks = [asyncio.create_task(analyze(c)) for c in companies]
                done_n = 0
                try:
                    for fut in asyncio.as_completed(tasks):
                        p = await fut
                        done_n += 1
                        self.analyzed += 1
                        if p.verdict is not Verdict.OUT and found < req.max_results:
                            found += 1
                            results.append(p)
                        self.on_prospect(p)
                        self.on_progress(ProgressEvent(
                            "analyze", f"Analyse — {loc_label} ({done_n}/{len(companies)})",
                            current=done_n, total=len(companies), found=found))
                        if found >= req.max_results:
                            break
                finally:
                    for t in tasks:
                        t.cancel()

            self.on_progress(ProgressEvent(
                "done", f"Terminé : {found} prospect(s) retenu(s) sur {self.analyzed} analysés",
                current=1, total=1, found=found))
            return results

    async def _search(self, providers: list[CompanyProvider], term: str, country, loc, limit: int
                      ) -> list[Company]:
        for prov in list(providers):
            try:
                return await prov.search(term, country, loc, limit)
            except ProviderError as exc:
                msg = f"{exc} — bascule sur OpenStreetMap"
                if msg not in self.warnings:
                    self.warnings.append(msg)
                    self.on_progress(ProgressEvent("search", "⚠ " + msg))
                providers.remove(prov)
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("Fournisseur %s: %s", prov.name, exc)
        return []


def run_sync(settings: Settings, req: SearchRequest, **cbs) -> list[Prospect]:
    """Point d'entrée synchrone (CLI / tests)."""
    return asyncio.run(Pipeline(settings, **cbs).run(req))
