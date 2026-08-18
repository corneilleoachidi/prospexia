"""France — API « Recherche d'entreprises » (https://recherche-entreprises.api.gouv.fr), gratuite, sans clé.

Renvoie SIREN/SIRET, forme juridique, NAF, dirigeants, effectif, date de création, état.
Limite d'usage : ~7 requêtes/seconde (respectée par un verrou + tempo).
"""
from __future__ import annotations

import asyncio
import logging
import re

import httpx

from prospexia.core.models import Company, LegalInfo

from .base import RegistryProvider, name_similarity

log = logging.getLogger(__name__)
_URL = "https://recherche-entreprises.api.gouv.fr/search"
_lock = asyncio.Semaphore(4)

NATURE_JURIDIQUE = {
    "1000": "Entrepreneur individuel", "5202": "SNC", "5306": "SCA", "5308": "SCA",
    "5410": "SARL nationale", "5415": "SARL d'économie mixte", "5426": "SARL immobilière",
    "5430": "SARL d'HLM", "5460": "Autre SARL", "5470": "SARL d'intérêt collectif",
    "5485": "SARL d'exercice libéral", "5498": "EURL", "5499": "SARL",
    "5505": "SA à conseil d'administration", "5510": "SA d'économie mixte", "5599": "SA",
    "5605": "SA à directoire", "5699": "SA à directoire", "5710": "SAS", "5720": "SASU",
    "5785": "SELAS", "5800": "Société européenne", "6100": "Caisse d'épargne",
    "6220": "GIE", "6316": "CUMA", "6317": "SCA (coopérative agricole)",
    "6521": "SCPI", "6532": "SCI de construction-vente", "6533": "GAEC", "6534": "GFA",
    "6540": "SCI", "6541": "SCI", "6558": "SCM", "6561": "SCP", "6585": "SCP", "6588": "SCP",
    "6589": "Société civile", "6595": "Caisse locale", "6599": "Société civile",
    "6901": "Autre personne morale de droit privé", "9210": "Association non déclarée",
    "9220": "Association déclarée", "9221": "Association d'insertion", "9222": "Association intermédiaire",
    "9223": "Groupement d'employeurs", "9224": "Association d'avocats", "9230": "Association d'utilité publique",
    "9240": "Congrégation", "9260": "Association de droit local", "9300": "Fondation",
}
TRANCHE_EFFECTIF = {
    "NN": "Non employeur", "00": "0 salarié", "01": "1 ou 2", "02": "3 à 5", "03": "6 à 9",
    "11": "10 à 19", "12": "20 à 49", "21": "50 à 99", "22": "100 à 199", "31": "200 à 249",
    "32": "250 à 499", "41": "500 à 999", "42": "1 000 à 1 999", "51": "2 000 à 4 999",
    "52": "5 000 à 9 999", "53": "10 000 et plus",
}
NAF_LABELS = {  # libellés des codes les plus fréquents pour nos secteurs (extrait)
    "43.22A": "Travaux d'installation d'eau et de gaz", "43.22B": "Travaux d'installation d'équipements thermiques",
    "43.21A": "Travaux d'installation électrique", "43.32A": "Travaux de menuiserie bois et PVC",
    "43.34Z": "Travaux de peinture et vitrerie", "43.91B": "Travaux de couverture", "43.99C": "Travaux de maçonnerie générale",
    "43.33Z": "Travaux de revêtement des sols et des murs", "41.20A": "Construction de maisons individuelles",
    "81.30Z": "Services d'aménagement paysager", "71.11Z": "Activités d'architecture",
    "56.10A": "Restauration traditionnelle", "56.10C": "Restauration de type rapide", "56.30Z": "Débits de boissons",
    "10.71C": "Boulangerie et boulangerie-pâtisserie", "10.71B": "Cuisson de produits de boulangerie",
    "47.22Z": "Commerce de détail de viandes", "56.21Z": "Services des traiteurs",
    "96.02A": "Coiffure", "96.02B": "Soins de beauté", "96.04Z": "Entretien corporel", "93.13Z": "Activités des centres de culture physique",
    "86.23Z": "Pratique dentaire", "86.90E": "Activités des professionnels de la rééducation", "75.00Z": "Activités vétérinaires",
    "47.78A": "Commerces de détail d'optique", "47.73Z": "Commerce de détail de produits pharmaceutiques",
    "45.20A": "Entretien et réparation de véhicules automobiles légers", "45.20B": "Entretien et réparation d'autres véhicules automobiles",
    "45.11Z": "Commerce de voitures et de véhicules automobiles légers", "85.53Z": "Enseignement de la conduite",
    "47.76Z": "Commerce de détail de fleurs", "47.71Z": "Commerce de détail d'habillement", "47.77Z": "Commerce de détail d'horlogerie-bijouterie",
    "47.61Z": "Commerce de détail de livres", "47.59A": "Commerce de détail de meubles", "96.01B": "Blanchisserie-teinturerie de détail",
    "69.10Z": "Activités juridiques", "69.20Z": "Activités comptables", "68.31Z": "Agences immobilières",
    "66.22Z": "Activités des agents et courtiers d'assurances", "49.42Z": "Services de déménagement", "81.21Z": "Nettoyage courant des bâtiments",
    "80.10Z": "Activités de sécurité privée", "74.20Z": "Activités photographiques", "18.12Z": "Autre imprimerie",
    "49.32Z": "Transports de voyageurs par taxis", "88.91A": "Accueil de jeunes enfants", "85.59B": "Autres enseignements",
    "55.10Z": "Hôtels et hébergement similaire", "55.20Z": "Hébergement touristique", "55.30Z": "Terrains de camping",
    "79.11Z": "Activités des agences de voyage", "01.21Z": "Culture de la vigne", "11.02A": "Fabrication de vins effervescents",
    "25.62B": "Mécanique industrielle", "49.41A": "Transports routiers de fret interurbains", "49.41B": "Transports routiers de fret de proximité",
}


def vat_number(siren: str) -> str:
    if not re.fullmatch(r"\d{9}", siren):
        return ""
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


class FranceRegistry(RegistryProvider):
    name = "france"

    async def lookup(self, company: Company) -> LegalInfo | None:
        postal = _postal_code(company.address)
        candidates: list[dict] = []
        try:
            candidates = await self._search(company.name)
            if not candidates and company.city:
                candidates = await self._search(f"{company.name} {company.city}")
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("Registre FR indisponible pour %s: %s", company.name, exc)
            return LegalInfo(registry="Recherche d'entreprises (api.gouv.fr)",
                             source_url=_search_url(company.name), matched=False)

        best, best_score = None, 0.0
        for c in candidates:
            score = _match_score(company, c, postal)
            if score > best_score:
                best, best_score = c, score
        if not best or best_score < 0.55:
            return LegalInfo(registry="Recherche d'entreprises (api.gouv.fr)",
                             source_url=_search_url(company.name), matched=False, confidence=best_score)
        return _to_legal(best, best_score)

    async def _search(self, q: str) -> list[dict]:
        params = {"q": q, "per_page": 10, "page": 1}
        async with _lock:
            resp = await self.client.get(_URL, params=params, timeout=15)
            await asyncio.sleep(0.2)
        if resp.status_code == 429:
            await asyncio.sleep(2)
            resp = await self.client.get(_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("results", []) or []


def _postal_code(address: str) -> str:
    m = re.search(r"\b(\d{5})\b", address or "")
    return m.group(1) if m else ""


def _search_url(name: str) -> str:
    from urllib.parse import quote_plus
    return "https://annuaire-entreprises.data.gouv.fr/rechercher?terme=" + quote_plus(name)


def _match_score(company: Company, c: dict, postal: str) -> float:
    names = [c.get("nom_complet") or "", c.get("nom_raison_sociale") or "", c.get("sigle") or ""]
    siege = c.get("siege") or {}
    for e in c.get("matching_etablissements") or []:
        for ens in (e.get("liste_enseignes") or []):
            names.append(ens)
        if e.get("nom_commercial"):
            names.append(e["nom_commercial"])
    if siege.get("nom_commercial"):
        names.append(siege["nom_commercial"])
    for ens in siege.get("liste_enseignes") or []:
        names.append(ens)
    sim = max((name_similarity(company.name, n) for n in names if n), default=0.0)

    postal_bonus = 0.0
    codes = {siege.get("code_postal", "")} | {e.get("code_postal", "") for e in c.get("matching_etablissements") or []}
    if postal:
        if postal in codes:
            postal_bonus = 0.15
        elif any(code and code[:2] == postal[:2] for code in codes):
            postal_bonus = 0.05
        else:
            postal_bonus = -0.15
    if c.get("etat_administratif") == "C":
        postal_bonus -= 0.1
    return max(0.0, min(1.0, sim + postal_bonus))


def _to_legal(c: dict, confidence: float) -> LegalInfo:
    siege = c.get("siege") or {}
    siren = c.get("siren", "")
    managers = []
    for d in c.get("dirigeants") or []:
        if d.get("type_dirigeant") == "personne morale":
            managers.append(f"{d.get('denomination', '')} ({d.get('qualite', '')})".strip())
        else:
            full = f"{(d.get('prenoms') or '').title()} {(d.get('nom') or '').upper()}".strip()
            managers.append(f"{full} ({d.get('qualite', '')})" if d.get("qualite") else full)
    naf = c.get("activite_principale") or siege.get("activite_principale") or ""
    return LegalInfo(
        registry="Recherche d'entreprises (api.gouv.fr)",
        identifier=siren, identifier_label="SIREN",
        secondary_id=siege.get("siret", ""), secondary_label="SIRET (siège)",
        legal_name=c.get("nom_complet") or c.get("nom_raison_sociale") or "",
        legal_form=NATURE_JURIDIQUE.get(c.get("nature_juridique", ""), c.get("nature_juridique", "") or ""),
        activity_code=naf, activity_label=NAF_LABELS.get(naf, ""),
        creation_date=c.get("date_creation") or siege.get("date_creation") or "",
        headcount=TRANCHE_EFFECTIF.get(c.get("tranche_effectif_salarie") or "", ""),
        status=("En liquidation" if any("liquidateur" in m.lower() for m in managers)
                else "Active" if c.get("etat_administratif") == "A"
                else "Cessée" if c.get("etat_administratif") == "C" else ""),
        address=siege.get("adresse", ""),
        managers=managers,
        vat_number=vat_number(siren),
        source_url=f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else "",
        confidence=round(confidence, 2),
        matched=True,
    )
