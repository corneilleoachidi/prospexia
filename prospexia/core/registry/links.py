"""Registres sans API ouverte : on fournit un lien de recherche pré-rempli."""
from __future__ import annotations

from urllib.parse import quote_plus

import httpx

from prospexia.core.models import Company, LegalInfo
from prospexia.data.countries import Country

from .base import RegistryProvider

# {name} est remplacé par le nom de l'entreprise (URL-encodé)
SEARCH_URLS: dict[str, tuple[str, str]] = {
    "BE": ("Banque-Carrefour des Entreprises (KBO/BCE)",
           "https://kbopub.economie.fgov.be/kbopub/zoeknaamfonetischform.html?searchWord={name}&lang=fr"),
    "CH": ("Zefix — Registre du commerce", "https://www.zefix.ch/fr/search/entity/list?name={name}"),
    "LU": ("Registre de Commerce et des Sociétés", "https://www.lbr.lu/mjrcs/jsp/secured/DisplayConsultDocumentsActionNotSecured.action?FROM_MENU=true&denomination={name}"),
    "GB": ("Companies House", "https://find-and-update.company-information.service.gov.uk/search/companies?q={name}"),
    "IE": ("Companies Registration Office", "https://core.cro.ie/search"),
    "DE": ("Handelsregister", "https://www.handelsregister.de/rp_web/erweitertesuche.xhtml"),
    "AT": ("Firmenbuch", "https://www.firmenbuch.at"),
    "NL": ("KVK Handelsregister", "https://www.kvk.nl/zoeken/?source=all&q={name}"),
    "ES": ("Registro Mercantil Central", "https://www.rmc.es/DenominacionesSociales.aspx"),
    "PT": ("Publicações de Atos Societários", "https://publicacoes.mj.pt/pesquisa.aspx"),
    "IT": ("Registro Imprese", "https://www.registroimprese.it/ricerca-libera-e-acquisto?q={name}"),
    "PL": ("KRS", "https://wyszukiwarka-krs.ms.gov.pl/"),
    "RO": ("ONRC", "https://portal.onrc.ro/ONRCPortalWeb/appmanager/myONRC/public"),
    "CZ": ("Obchodní rejstřík", "https://or.justice.cz/ias/ui/rejstrik-$firma?nazev={name}"),
    "DK": ("CVR", "https://datacvr.virk.dk/soegeresultater?fritekst={name}"),
    "NO": ("Brønnøysundregistrene", "https://www.brreg.no/sok/?q={name}"),
    "SE": ("Bolagsverket", "https://foretagsinfo.bolagsverket.se/sok-foretagsinformation-web/foretag/sok"),
    "FI": ("YTJ", "https://tietopalvelu.ytj.fi/yrityshaku.aspx?kielikoodi=1&nimi={name}"),
    "CA": ("Corporations Canada / REQ", "https://www.registreentreprises.gouv.qc.ca/RQAnonymeGR/GR/GR03/GR03A2_19A_PIU_RechEnt_PC/PageRechSimple.aspx"),
    "US": ("OpenCorporates", "https://opencorporates.com/companies?q={name}"),
    "MA": ("DirectInfo (OMPIC)", "https://www.directinfo.ma/"),
    "TN": ("Registre National des Entreprises", "https://www.registre-entreprises.tn/rne-public/#/"),
    "SN": ("RCCM Sénégal", "https://www.creationdentreprise.sn/rechercher-une-societe"),
    "CI": ("RCCM Côte d'Ivoire", "https://www.cepici.gouv.ci/"),
    "AU": ("ASIC Connect", "https://connectonline.asic.gov.au/RegistrySearch/faces/landing/SearchRegisters.jspx"),
    "IN": ("MCA", "https://www.mca.gov.in/content/mca/global/en/mca/master-data/MDS.html"),
    "BR": ("Consulta CNPJ", "https://cnpj.biz/procura/{name}"),
    "NG": ("CAC Public Search", "https://search.cac.gov.ng/home"),
    "KE": ("eCitizen BRS", "https://brs.ecitizen.go.ke/"),
    "ZA": ("CIPC", "https://eservices.cipc.co.za/Search.aspx"),
}


class LinkOnlyRegistry(RegistryProvider):
    name = "links"

    def __init__(self, client: httpx.AsyncClient, country: Country):
        super().__init__(client)
        self.country = country

    async def lookup(self, company: Company) -> LegalInfo | None:
        entry = SEARCH_URLS.get(self.country.code)
        if entry:
            label, tpl = entry
            url = tpl.replace("{name}", quote_plus(company.name))
        elif self.country.registry:
            label, url = "Registre officiel", self.country.registry
        else:
            return None
        return LegalInfo(registry=label, source_url=url, matched=False)
