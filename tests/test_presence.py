import httpx
import pytest

from prospexia.core.models import Company, WebsiteStatus
from prospexia.core.presence import _domain, _domain_matches, _name_tokens, check_website, web_presence
from prospexia.data.countries import COUNTRY_BY_CODE

NOW_HTML = '<html><head><meta name="viewport" content="width=device-width"><title>Chez Marcel</title></head><body>' + "x" * 3000 + "© 2026</body></html>"
OLD_HTML = "<html><head><title>Vieux site</title></head><body><marquee>Bienvenue</marquee>" + "x" * 2000 + "Copyright 2009</body></html>"


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)


async def test_no_website():
    async with _client(lambda r: httpx.Response(200)) as c:
        chk = await check_website(c, "")
    assert chk.status is WebsiteStatus.NONE


async def test_social_url_is_social_only():
    async with _client(lambda r: httpx.Response(200)) as c:
        chk = await check_website(c, "https://www.facebook.com/chezmarcel")
    assert chk.status is WebsiteStatus.SOCIAL_ONLY


async def test_modern_site_ok():
    async with _client(lambda r: httpx.Response(200, text=NOW_HTML, headers={"content-type": "text/html"})) as c:
        chk = await check_website(c, "https://chezmarcel.fr")
    assert chk.status is WebsiteStatus.OK
    assert chk.title == "Chez Marcel"
    assert chk.mobile_friendly is True


async def test_old_site_obsolete():
    async with _client(lambda r: httpx.Response(200, text=OLD_HTML, headers={"content-type": "text/html"})) as c:
        chk = await check_website(c, "http://vieux-site.fr")
    assert chk.status is WebsiteStatus.OBSOLETE
    assert chk.copyright_year == 2009
    assert "Pas de HTTPS" in chk.issues


async def test_http_error_is_dead():
    async with _client(lambda r: httpx.Response(503)) as c:
        chk = await check_website(c, "https://down.example")
    assert chk.status is WebsiteStatus.DEAD


async def test_connect_error_is_dead():
    def boom(_r):
        raise httpx.ConnectError("dns")
    async with _client(boom) as c:
        chk = await check_website(c, "https://nowhere.invalid")
    assert chk.status is WebsiteStatus.DEAD


def test_domain_helpers():
    assert _domain("https://www.Example.com/path") == "example.com"
    toks = _name_tokens("Le Plombier Gentleman SARL")
    assert toks == ["plombier", "gentleman"]
    assert _domain_matches("leplombiergentleman.com", toks)
    assert _domain_matches("plombier-gentleman.fr", toks)
    assert not _domain_matches("pagesjaunes.fr", toks)
    assert not _domain_matches("plombier.com", toks)


async def test_serpapi_presence_parses_socials_and_discovers_site():
    def handler(r: httpx.Request):
        assert r.url.host == "serpapi.com"
        return httpx.Response(200, json={"organic_results": [
            {"link": "https://www.leplombiergentleman.com/"},
            {"link": "https://www.facebook.com/leplombiergentleman"},
            {"link": "https://www.pagesjaunes.fr/pros/123"},
        ]})
    company = Company(name="Le Plombier Gentleman", city="Paris")
    async with _client(handler) as c:
        pres = await web_presence(c, company, COUNTRY_BY_CODE["FR"], "key")
    assert pres.search_engine == "serpapi"
    assert pres.search_hits == 3
    assert pres.socials == {"facebook": "https://www.facebook.com/leplombiergentleman"}
    assert pres.directories == ["pagesjaunes.fr"]
    assert pres.discovered_website == "https://www.leplombiergentleman.com/"


@pytest.mark.parametrize("status", [401, 500])
async def test_search_failure_marks_engine_unavailable(status):
    async with _client(lambda r: httpx.Response(status)) as c:
        pres = await web_presence(c, Company(name="X"), COUNTRY_BY_CODE["FR"], "key")
    assert pres.search_engine == ""
    assert pres.search_hits == 0


async def test_osm_provider_parses_jsonv2_and_filters_streets():
    from prospexia.core.providers.osm import OSMProvider
    payload = [
        {"category": "craft", "type": "plumber", "name": "Artisan Plombier", "display_name": "Artisan Plombier, Paris",
         "lat": "48.8", "lon": "2.3", "osm_id": 1, "osm_type": "node",
         "address": {"city": "Paris"}, "extratags": {"website": "https://ex.fr"}, "namedetails": {"name": "Artisan Plombier"}},
        {"category": "highway", "type": "residential", "name": "Chemin du Plombier", "display_name": "x", "osm_id": 2},
        {"category": "craft", "type": "plumber", "name": "Plombier", "display_name": "x", "osm_id": 3},
    ]
    async with _client(lambda r: httpx.Response(200, json=payload)) as c:
        res = await OSMProvider(c).search("Plombier", COUNTRY_BY_CODE["FR"], "Paris", 20)
    assert [r.name for r in res] == ["Artisan Plombier"]
    assert res[0].website == "https://ex.fr" and res[0].city == "Paris"
