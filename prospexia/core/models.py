"""Modèles de données partagés entre le pipeline, l'UI et l'export."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RelevanceMode(StrEnum):
    STRICT = "strict"        # aucun site web + présence en ligne très faible
    FLEXIBLE = "flexible"    # site absent, obsolète ou HS + présence faible

    @property
    def label(self) -> str:
        return "Strict" if self is RelevanceMode.STRICT else "Flexible"


class WebsiteStatus(StrEnum):
    NONE = "none"            # aucun site connu
    DEAD = "dead"            # site déclaré mais injoignable (DNS, timeout, 4xx/5xx)
    OBSOLETE = "obsolete"    # site joignable mais visiblement vieillissant / non maintenu
    SOCIAL_ONLY = "social"   # "site" = simple page Facebook/Instagram
    THIRD_PARTY = "platform" # "site" = fiche annuaire / plateforme de réservation (Planity, PagesJaunes…)
    OK = "ok"                # site fonctionnel et moderne

    @property
    def label(self) -> str:
        return {
            "none": "Aucun site",
            "dead": "Site HS",
            "obsolete": "Site obsolète",
            "social": "Réseau social seul",
            "platform": "Plateforme tierce seule",
            "ok": "Site OK",
        }[self.value]


class Verdict(StrEnum):
    PRIORITY = "priority"    # cible prioritaire
    TARGET = "target"        # cible
    OUT = "out"              # hors cible

    @property
    def label(self) -> str:
        return {"priority": "Prioritaire", "target": "Cible", "out": "Hors cible"}[self.value]


@dataclass
class SearchRequest:
    country_code: str
    sector_keys: list[str]                       # clés du catalogue
    custom_sectors: list[str] = field(default_factory=list)  # secteurs libres saisis en FR
    max_results: int = 20
    mode: RelevanceMode = RelevanceMode.STRICT


@dataclass
class Company:
    """Entreprise brute renvoyée par un fournisseur (Google Places, OSM…)."""
    name: str
    address: str = ""
    city: str = ""
    phone: str = ""
    website: str = ""
    sector: str = ""                 # libellé FR du secteur ayant produit ce résultat
    source: str = ""                 # "google" | "osm"
    rating: float | None = None
    reviews_count: int = 0
    lat: float | None = None
    lon: float | None = None
    source_id: str = ""
    maps_url: str = ""

    def dedupe_key(self) -> str:
        import re
        n = re.sub(r"[^a-z0-9]", "", self.name.lower())
        c = re.sub(r"[^a-z0-9]", "", (self.city or self.address[:20]).lower())
        return f"{n}|{c}"


@dataclass
class WebsiteCheck:
    status: WebsiteStatus = WebsiteStatus.NONE
    final_url: str = ""
    http_status: int | None = None
    https: bool = False
    mobile_friendly: bool | None = None
    copyright_year: int | None = None
    title: str = ""
    issues: list[str] = field(default_factory=list)   # raisons lisibles


@dataclass
class WebPresence:
    search_hits: int = 0                  # nb de résultats web pertinents pour le nom
    own_domain_in_results: bool = False
    socials: dict[str, str] = field(default_factory=dict)   # réseau -> URL
    directories: list[str] = field(default_factory=list)    # annuaires (pagesjaunes, yelp…)
    search_engine: str = ""               # "serpapi" | "duckduckgo" | "" (non évalué)
    skipped: bool = False                 # recherche volontairement ignorée (site déjà OK)
    discovered_website: str = ""          # site trouvé via la recherche alors que le fournisseur n'en listait pas


@dataclass
class LegalInfo:
    """Informations légales issues d'un registre officiel (ou lien de recherche si pas d'API)."""
    registry: str = ""                    # ex. "Recherche d'entreprises (api.gouv.fr)"
    identifier: str = ""                  # identifiant national principal (SIREN, CRN, KBO…)
    identifier_label: str = ""            # libellé de l'identifiant ("SIREN")
    secondary_id: str = ""                # ex. SIRET du siège
    secondary_label: str = ""
    legal_name: str = ""                  # dénomination officielle
    legal_form: str = ""                  # forme juridique
    activity_code: str = ""               # code NAF/APE ou équivalent
    activity_label: str = ""
    creation_date: str = ""               # AAAA-MM-JJ
    headcount: str = ""                   # tranche d'effectif
    status: str = ""                      # "Active" / "Cessée"
    address: str = ""                     # adresse du siège
    managers: list[str] = field(default_factory=list)   # "Prénom NOM (qualité)"
    vat_number: str = ""
    source_url: str = ""                  # fiche officielle ou lien de recherche
    confidence: float = 0.0               # 0-1 : qualité de l'appariement nom/adresse
    matched: bool = False                 # True si une fiche a été trouvée automatiquement


@dataclass
class Prospect:
    company: Company
    website: WebsiteCheck = field(default_factory=WebsiteCheck)
    presence: WebPresence = field(default_factory=WebPresence)
    legal: LegalInfo | None = None
    score: int = 0                        # 0 (invisible) -> 100 (très présent)
    verdict: Verdict = Verdict.OUT
    reasons: list[str] = field(default_factory=list)
    from_cache: bool = False
    cached_at: str = ""                   # date lisible de l'analyse en cache

    @property
    def opportunity(self) -> str:
        """Prestation à proposer, déduite du diagnostic."""
        st = self.website.status
        if st in (WebsiteStatus.NONE, WebsiteStatus.SOCIAL_ONLY, WebsiteStatus.THIRD_PARTY, WebsiteStatus.DEAD):
            return "Création de site web"
        if st is WebsiteStatus.OBSOLETE:
            return "Refonte de site + SEO"
        return "Optimisation SEO"


@dataclass
class ProgressEvent:
    stage: str            # "translate" | "search" | "analyze" | "done"
    message: str
    current: int = 0
    total: int = 0
    found: int = 0        # prospects retenus jusqu'ici
