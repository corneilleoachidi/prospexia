import httpx

from prospexia.core.cache import ResultCache
from prospexia.core.models import Company, LegalInfo, Prospect, WebPresence, WebsiteCheck, WebsiteStatus
from prospexia.core.registry.base import name_similarity, normalize_name
from prospexia.core.registry.france import FranceRegistry, vat_number
from prospexia.core.registry.links import LinkOnlyRegistry
from prospexia.data.countries import COUNTRY_BY_CODE


def test_cache_roundtrip_and_expiry(tmp_path):
    c = ResultCache(tmp_path / "c.sqlite", ttl_days=30)
    key = ResultCache.query_key("google", "Plombier", "FR", "Lyon", 20)
    assert c.get_query(key) is None
    c.put_query(key, [Company(name="A", city="Lyon", website="https://a.fr")])
    got = c.get_query(key)
    assert got and got[0].name == "A" and got[0].website == "https://a.fr"

    p = Prospect(company=Company(name="A", city="Lyon"))
    p.website = WebsiteCheck(status=WebsiteStatus.OBSOLETE, issues=["Pas de HTTPS"])
    p.presence = WebPresence(search_hits=3, socials={"facebook": "f"}, search_engine="serpapi")
    p.legal = LegalInfo(identifier="123", matched=True)
    c.put_analysis(p)
    ts, w, pr, lg = c.get_analysis(Company(name="a!", city="LYON"))  # même clé de dédup
    assert w.status is WebsiteStatus.OBSOLETE and pr.socials == {"facebook": "f"} and lg.identifier == "123"
    assert c.stats() == {"queries": 1, "analyses": 1}

    # expiration
    c.conn.execute("UPDATE analyses SET ts = ts - 40*86400"); c.conn.commit()
    assert c.get_analysis(Company(name="A", city="Lyon")) is None
    c.clear(); assert c.stats() == {"queries": 0, "analyses": 0}
    c.close()


def test_name_helpers_and_vat():
    assert normalize_name("Le Plombier Gentleman SAS") == "le plombier gentleman"
    assert name_similarity("Le Plombier Gentleman", "LE PLOMBIER GENTLEMAN (PG)") > 0.8
    assert name_similarity("Chez Marcel", "Boulangerie Dupont") < 0.4
    assert vat_number("814345666") == "FR54814345666"
    assert vat_number("abc") == ""


async def test_france_registry_matches_best_candidate():
    payload = {"results": [
        {"siren": "111111111", "nom_complet": "PLOMBERIE DURAND", "nature_juridique": "5499", "etat_administratif": "A",
         "activite_principale": "43.22A", "date_creation": "2010-01-01", "tranche_effectif_salarie": "02",
         "siege": {"siret": "11111111100011", "code_postal": "69003", "adresse": "1 RUE X 69003 LYON"},
         "dirigeants": [{"nom": "DURAND", "prenoms": "JEAN", "qualite": "Gérant", "type_dirigeant": "personne physique"}]},
        {"siren": "222222222", "nom_complet": "PLOMBERIE DURAND", "nature_juridique": "5710", "etat_administratif": "A",
         "siege": {"siret": "22222222200011", "code_postal": "75001", "adresse": "PARIS"}, "dirigeants": []},
    ]}
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))) as c:
        lg = await FranceRegistry(c).lookup(Company(name="Plomberie Durand", address="12 rue Y, 69003 Lyon", city="Lyon"))
    assert lg.matched and lg.identifier == "111111111" and lg.legal_form == "SARL"
    assert lg.activity_label.startswith("Travaux d'installation d'eau")
    assert lg.managers == ["Jean DURAND (Gérant)"] and lg.headcount == "3 à 5"
    assert lg.vat_number.startswith("FR") and "111111111" in lg.source_url


async def test_france_registry_no_match_gives_search_link():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"results": []}))) as c:
        lg = await FranceRegistry(c).lookup(Company(name="Inconnu"))
    assert lg is not None and not lg.matched and "rechercher?terme=Inconnu" in lg.source_url


async def test_link_only_registry():
    async with httpx.AsyncClient() as c:
        lg = await LinkOnlyRegistry(c, COUNTRY_BY_CODE["BE"]).lookup(Company(name="Chez Marcel"))
    assert not lg.matched and "searchWord=Chez+Marcel" in lg.source_url
