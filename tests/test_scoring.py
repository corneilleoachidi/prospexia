from prospexia.core.models import (
    Company,
    Prospect,
    RelevanceMode,
    Verdict,
    WebPresence,
    WebsiteCheck,
    WebsiteStatus,
)
from prospexia.core.scoring import score_prospect


def _p(status: WebsiteStatus, socials=None, hits=0, reviews=0, engine="serpapi") -> Prospect:
    p = Prospect(company=Company(name="Test", reviews_count=reviews))
    p.website = WebsiteCheck(status=status)
    p.presence = WebPresence(search_hits=hits, socials=socials or {}, search_engine=engine)
    return p


def test_no_site_invisible_is_priority_in_strict():
    p = _p(WebsiteStatus.NONE)
    score_prospect(p, RelevanceMode.STRICT)
    assert p.verdict is Verdict.PRIORITY
    assert p.score == 0
    assert p.opportunity == "Création de site web"


def test_ok_site_is_out_in_both_modes():
    for mode in RelevanceMode:
        p = _p(WebsiteStatus.OK, socials={"facebook": "x"}, hits=10, reviews=120)
        score_prospect(p, mode)
        assert p.verdict is Verdict.OUT
        assert p.score > 60


def test_obsolete_site_is_target_only_in_flexible():
    strict = _p(WebsiteStatus.OBSOLETE, hits=2)
    score_prospect(strict, RelevanceMode.STRICT)
    assert strict.verdict is Verdict.OUT
    flex = _p(WebsiteStatus.OBSOLETE, hits=2)
    score_prospect(flex, RelevanceMode.FLEXIBLE)
    assert flex.verdict is Verdict.TARGET
    assert flex.opportunity == "Refonte de site + SEO"


def test_dead_site_priority_in_flexible():
    p = _p(WebsiteStatus.DEAD)
    score_prospect(p, RelevanceMode.FLEXIBLE)
    assert p.verdict is Verdict.PRIORITY


def test_social_only_counts_as_no_site_in_strict():
    p = _p(WebsiteStatus.SOCIAL_ONLY, socials={"facebook": "x"}, hits=3)
    score_prospect(p, RelevanceMode.STRICT)
    assert p.verdict is Verdict.TARGET


def test_unavailable_engine_is_flagged_not_invisible():
    p = _p(WebsiteStatus.NONE, engine="")
    score_prospect(p, RelevanceMode.STRICT)
    assert any("non évaluée" in r for r in p.reasons)
    assert not any("Invisible" in r for r in p.reasons)


def test_third_party_platform_is_target_in_strict_and_priority_in_flexible():
    p = _p(WebsiteStatus.THIRD_PARTY, socials={"instagram": "x"}, hits=5, reviews=10)
    score_prospect(p, RelevanceMode.STRICT)
    assert p.verdict is Verdict.TARGET
    assert p.opportunity == "Création de site web"
    busy = _p(WebsiteStatus.THIRD_PARTY, socials={"instagram": "x"}, hits=5, reviews=200)
    score_prospect(busy, RelevanceMode.STRICT)
    assert busy.verdict is Verdict.OUT      # présence trop forte pour le mode Strict
    score_prospect(busy, RelevanceMode.FLEXIBLE)
    assert busy.verdict is Verdict.TARGET
    p2 = _p(WebsiteStatus.THIRD_PARTY, hits=2)
    score_prospect(p2, RelevanceMode.FLEXIBLE)
    assert p2.verdict is Verdict.PRIORITY


def test_skipped_search_reason():
    p = _p(WebsiteStatus.OK, engine="")
    p.presence.skipped = True
    score_prospect(p, RelevanceMode.FLEXIBLE)
    assert p.verdict is Verdict.OUT
    assert any("ignorée" in r for r in p.reasons)
