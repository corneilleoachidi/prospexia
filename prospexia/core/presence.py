"""Analyse de la présence en ligne : état du site web + visibilité sur les moteurs / réseaux."""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import re
import time
from urllib.parse import quote_plus, urlparse

import httpx

from prospexia.core.models import Company, WebPresence, WebsiteCheck, WebsiteStatus
from prospexia.data.countries import Country

log = logging.getLogger(__name__)

SOCIAL_DOMAINS = {
    "facebook.com": "facebook", "fb.com": "facebook", "instagram.com": "instagram",
    "linkedin.com": "linkedin", "twitter.com": "x", "x.com": "x", "tiktok.com": "tiktok",
    "youtube.com": "youtube", "pinterest.com": "pinterest",
}
DIRECTORY_DOMAINS = (
    "pagesjaunes", "yelp", "tripadvisor", "societe.com", "kompass", "europages", "yellowpages",
    "pappers", "infogreffe", "annuaire", "hotfrog", "cylex", "trustpilot", "foursquare",
    "gelbeseiten", "paginegialle", "paginasamarillas", "goudengids", "112.ch", "local.ch",
    "thefork", "lafourchette", "doctolib", "ubereats", "deliveroo", "booking.com", "airbnb",
    "mappy", "waze", "google.", "bing.com", "apple.com/maps",
)
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _domain(url: str) -> str:
    try:
        host = urlparse(url if "://" in url else "http://" + url).netloc.lower()
    except ValueError:
        return ""
    return host.removeprefix("www.")


def _social_of(url: str) -> str | None:
    d = _domain(url)
    for dom, name in SOCIAL_DOMAINS.items():
        if d == dom or d.endswith("." + dom):
            return name
    return None


# --------------------------------------------------------------------------- site web
async def check_website(client: httpx.AsyncClient, url: str) -> WebsiteCheck:
    chk = WebsiteCheck()
    if not url.strip():
        chk.status = WebsiteStatus.NONE
        chk.issues.append("Aucun site web déclaré")
        return chk
    if _social_of(url):
        chk.status = WebsiteStatus.SOCIAL_ONLY
        chk.final_url = url
        chk.issues.append(f"Le « site » est une page {_social_of(url)}")
        return chk
    if "://" not in url:
        url = "http://" + url
    try:
        resp = await client.get(url, headers={"User-Agent": _UA}, follow_redirects=True)
    except httpx.HTTPError as exc:
        chk.status = WebsiteStatus.DEAD
        chk.issues.append(f"Site injoignable ({type(exc).__name__})")
        return chk
    chk.http_status = resp.status_code
    chk.final_url = str(resp.url)
    chk.https = resp.url.scheme == "https"
    if resp.status_code >= 400:
        chk.status = WebsiteStatus.DEAD
        chk.issues.append(f"Erreur HTTP {resp.status_code}")
        return chk
    if _social_of(chk.final_url):
        chk.status = WebsiteStatus.SOCIAL_ONLY
        chk.issues.append("Redirige vers un réseau social")
        return chk

    html = resp.text[:400_000] if "text/html" in resp.headers.get("content-type", "") else ""
    low = html.lower()
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    chk.title = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else ""
    chk.mobile_friendly = 'name="viewport"' in low or "name='viewport'" in low
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d{2}|19\d{2})", low)]
    if years:
        chk.copyright_year = max(years)

    now = dt.date.today().year
    obsolete_points = 0
    if not chk.https:
        chk.issues.append("Pas de HTTPS"); obsolete_points += 2
    if chk.mobile_friendly is False:
        chk.issues.append("Non adapté mobile (pas de viewport)"); obsolete_points += 2
    if chk.copyright_year and chk.copyright_year <= now - 3:
        chk.issues.append(f"Copyright {chk.copyright_year}"); obsolete_points += 2
    if html and len(html) < 1500:
        chk.issues.append("Page quasi vide"); obsolete_points += 2
    for marker, label in (
        ("en construction", "En construction"), ("under construction", "En construction"),
        ("coming soon", "Coming soon"), ("site en cours de création", "En construction"),
        ("domaine parké", "Domaine parké"), ("this domain is parked", "Domaine parké"),
        ("buy this domain", "Domaine à vendre"), ("ce domaine est à vendre", "Domaine à vendre"),
        ("wix.com/website-template", "Template Wix non personnalisé"),
        ("<frameset", "Frames HTML obsolètes"), ("<marquee", "Balise <marquee>"),
        ("adobe flash", "Flash"), ("swfobject", "Flash"),
    ):
        if marker in low:
            chk.issues.append(label); obsolete_points += 3
    if "wordpress" in low and re.search(r"wordpress\s*[/ ]\s*[2-4]\.", low):
        chk.issues.append("WordPress très ancien"); obsolete_points += 3

    chk.status = WebsiteStatus.OBSOLETE if obsolete_points >= 3 else WebsiteStatus.OK
    return chk


# --------------------------------------------------------------------------- moteurs de recherche
async def web_presence(client: httpx.AsyncClient, company: Company, country: Country,
                       serpapi_key: str) -> WebPresence:
    pres = WebPresence()
    q = f'"{company.name}" {company.city or country.name_fr}'
    links: list[str] = []
    try:
        if serpapi_key:
            links = await _serpapi(client, q, country, serpapi_key)
            pres.search_engine = "serpapi"
        else:
            links = await _duckduckgo(client, q)
            pres.search_engine = "duckduckgo"
    except SearchUnavailable as exc:
        log.info("Recherche web indisponible pour %s: %s", company.name, exc)
        pres.search_engine = ""
        return pres
    except Exception as exc:  # noqa: BLE001 — la recherche ne doit jamais bloquer le pipeline
        log.warning("Recherche web échouée pour %s: %s", company.name, exc)
        pres.search_engine = ""
        return pres

    own = _domain(company.website) if company.website else ""
    name_tokens = _name_tokens(company.name)
    for link in links:
        d = _domain(link)
        if not d:
            continue
        soc = _social_of(link)
        if soc:
            pres.socials.setdefault(soc, link)
            continue
        if any(x in d for x in DIRECTORY_DOMAINS):
            pres.directories.append(d)
            continue
        if own and (d == own or d.endswith("." + own)):
            pres.own_domain_in_results = True
        elif not own and not pres.discovered_website and _domain_matches(d, name_tokens):
            pres.discovered_website = link
    pres.search_hits = len(links)
    return pres


def _name_tokens(name: str) -> list[str]:
    import unicodedata
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    tokens = re.findall(r"[a-z0-9]+", ascii_name.lower())
    stop = {"le", "la", "les", "de", "du", "des", "et", "the", "and", "sarl", "sas", "eurl", "sa",
            "ltd", "gmbh", "srl", "bv", "inc", "llc", "chez", "maison", "atelier", "cabinet",
            "entreprise", "ets", "sté", "societe"}
    return [t for t in tokens if len(t) >= 3 and t not in stop]


def _domain_matches(domain: str, tokens: list[str]) -> bool:
    """Le domaine « ressemble » au nom : tous les tokens significatifs (ou une concaténation) y figurent."""
    if not tokens:
        return False
    host = domain.split(".")[0] if domain.count(".") == 1 else ".".join(domain.split(".")[:-1])
    host = re.sub(r"[^a-z0-9]", "", host)
    joined = "".join(tokens)
    if len(joined) >= 6 and joined in host:
        return True
    hits = sum(1 for t in tokens if t in host)
    return hits >= max(1, len(tokens) - 1) and hits >= (2 if len(tokens) >= 2 else 1)


async def _serpapi(client: httpx.AsyncClient, q: str, country: Country, key: str) -> list[str]:
    params = {"engine": "google", "q": q, "gl": country.code.lower(), "hl": country.lang,
              "num": 10, "api_key": key}
    resp = await client.get("https://serpapi.com/search.json", params=params)
    if resp.status_code == 401:
        raise RuntimeError("Clé SerpAPI invalide")
    resp.raise_for_status()
    data = resp.json()
    links = [r.get("link", "") for r in data.get("organic_results", [])]
    kg = data.get("knowledge_graph", {})
    if kg.get("website"):
        links.append(kg["website"])
    for prof in kg.get("profiles", []) or []:
        if prof.get("link"):
            links.append(prof["link"])
    return [x for x in links if x]


class SearchUnavailable(RuntimeError):
    """Le moteur de recherche refuse les requêtes (anti-bot / quota)."""


_ddg_lock = asyncio.Lock()
_ddg_blocked_until = 0.0


async def _duckduckgo(client: httpx.AsyncClient, q: str) -> list[str]:
    global _ddg_blocked_until
    if time.monotonic() < _ddg_blocked_until:
        raise SearchUnavailable("DuckDuckGo temporairement bloqué (anti-bot)")
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(q)
    async with _ddg_lock:  # DDG bloque vite : une requête à la fois, espacée
        resp = await client.get(url, headers={"User-Agent": _UA}, follow_redirects=True)
        await asyncio.sleep(1.5)
    if resp.status_code == 202 or "anomaly" in resp.text[:2000].lower():
        _ddg_blocked_until = time.monotonic() + 120
        raise SearchUnavailable("DuckDuckGo a déclenché une vérification anti-bot")
    resp.raise_for_status()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    links: list[str] = []
    for a in soup.select("a.result__a, a.result__url"):
        href = a.get("href", "")
        if "uddg=" in href:
            from urllib.parse import parse_qs, unquote
            href = unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
        if href.startswith("http") and href not in links:
            links.append(href)
    return links[:10]
