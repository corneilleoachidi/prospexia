"""Score de présence en ligne (0 = invisible, 100 = très présent) et verdict selon le mode."""
from __future__ import annotations

from prospexia.core.models import Prospect, RelevanceMode, Verdict, WebsiteStatus

_WEBSITE_POINTS = {
    WebsiteStatus.NONE: 0,
    WebsiteStatus.SOCIAL_ONLY: 8,
    WebsiteStatus.THIRD_PARTY: 8,
    WebsiteStatus.DEAD: 10,
    WebsiteStatus.OBSOLETE: 28,
    WebsiteStatus.OK: 60,
}


def score_prospect(p: Prospect, mode: RelevanceMode) -> None:
    """Calcule score, verdict et raisons, en place."""
    reasons: list[str] = []
    score = _WEBSITE_POINTS[p.website.status]
    reasons.append(p.website.status.label)
    reasons.extend(p.website.issues[:3])

    n_soc = len(p.presence.socials)
    if n_soc:
        score += min(n_soc * 6, 18)
        reasons.append("Réseaux : " + ", ".join(sorted(p.presence.socials)))
    elif not p.presence.skipped:
        reasons.append("Aucun réseau social trouvé")

    hits = p.presence.search_hits
    if p.presence.skipped:
        reasons.append("Recherche web ignorée (site déjà fonctionnel)")
    elif not p.presence.search_engine:
        reasons.append("Visibilité web non évaluée (moteur indisponible)")
    elif hits == 0:
        reasons.append("Invisible sur les moteurs de recherche")
    elif hits <= 3:
        score += 4; reasons.append(f"{hits} résultat(s) web")
    elif hits <= 7:
        score += 8; reasons.append(f"{hits} résultats web")
    else:
        score += 12; reasons.append(f"{hits}+ résultats web")
    if p.presence.own_domain_in_results:
        score += 6
    if p.presence.directories:
        score += min(len(set(p.presence.directories)) * 2, 6)

    rc = p.company.reviews_count
    if rc >= 100:
        score += 10; reasons.append(f"{rc} avis Google")
    elif rc >= 30:
        score += 6; reasons.append(f"{rc} avis Google")
    elif rc >= 5:
        score += 3

    if p.from_cache and p.cached_at:
        reasons.append(f"Analyse en cache du {p.cached_at}")
    p.score = max(0, min(100, score))
    p.reasons = reasons

    st = p.website.status
    if mode is RelevanceMode.STRICT:
        no_own_site = (WebsiteStatus.NONE, WebsiteStatus.SOCIAL_ONLY, WebsiteStatus.THIRD_PARTY)
        eligible = st in no_own_site and p.score <= 30
        priority = st is WebsiteStatus.NONE and p.score <= 15
    else:
        eligible = st is not WebsiteStatus.OK and p.score <= 50
        priority = st in (WebsiteStatus.NONE, WebsiteStatus.DEAD, WebsiteStatus.SOCIAL_ONLY,
                          WebsiteStatus.THIRD_PARTY) and p.score <= 25
    p.verdict = Verdict.PRIORITY if (eligible and priority) else Verdict.TARGET if eligible else Verdict.OUT
