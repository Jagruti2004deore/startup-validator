from app.scoring import (
    build_score, competitor_key, count_competitors, crowdedness, matched_pricing,
    VERDICT_UNCLEAR, VERDICT_RISKY, VERDICT_PROMISING, VERDICT_CAUTION,
)

NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]


def comps(n):
    return [{"category": "competitor", "text": f"{NAMES[i]} offers a study tool"} for i in range(n)]


def claim(category, text=None):
    return {"category": category, "text": text or f"{category} fact"}


def prices():
    """Two pricing claims that name competitors Alpha and Beta."""
    return [claim("pricing", "Alpha charges $5 a month"), claim("pricing", "Beta charges $7 a month")]


def full_set(n_comps=4, gap=True):
    verified = comps(n_comps) + prices() + [
        claim("demand_signal"), claim("market_size"),
        claim("recent_activity"), claim("failure_or_risk"),
    ]
    if gap:
        verified.append(claim("differentiation_gap"))
    return verified


def test_full_evidence_is_promising():
    score = build_score(full_set(), memory_checked=True)
    assert score["evidence_score"] == 8
    assert score["crowdedness"] == "medium"
    assert score["verdict"] == VERDICT_PROMISING


def test_too_little_evidence_is_unclear():
    score = build_score(comps(2), memory_checked=True)
    assert score["verdict"] == VERDICT_UNCLEAR


def test_crowded_market_without_gap_is_risky():
    verified = comps(8) + prices() + [claim("demand_signal"), claim("market_size")]
    score = build_score(verified, memory_checked=True)
    assert score["crowdedness"] == "high"
    assert score["verdict"] == VERDICT_RISKY


def test_crowded_market_with_gap_is_only_caution():
    score = build_score(full_set(n_comps=8), memory_checked=True)
    assert score["verdict"] == VERDICT_CAUTION


def test_conflict_with_past_notes_blocks_promising():
    verified = full_set() + [claim("conflict_with_past_notes")]
    score = build_score(verified, memory_checked=True)
    assert score["has_conflict"] is True
    assert score["verdict"] == VERDICT_CAUTION


def test_missing_memory_check_costs_one_point():
    score = build_score(full_set(), memory_checked=False)
    assert score["evidence_score"] == 7
    assert score["verdict"] == VERDICT_PROMISING


def test_crowdedness_thresholds():
    assert crowdedness(0) == "unknown"
    assert crowdedness(2) == "low"
    assert crowdedness(3) == "medium"
    assert crowdedness(6) == "medium"
    assert crowdedness(7) == "high"


def test_same_company_counts_once():
    verified = [
        {"category": "competitor", "text": "Kahoot+ Study lets groups quiz"},
        {"category": "competitor", "text": "Kahoot+ Study also sells plans"},
    ]
    assert competitor_key(verified[0]["text"]) == competitor_key(verified[1]["text"])
    assert count_competitors(verified) == 1


def test_gap_only_counts_when_verified():
    score = build_score(comps(4), memory_checked=True)
    assert score["has_gap"] is False


def test_reasons_are_readable_text():
    score = build_score(full_set(), memory_checked=True)
    assert score["reasons"] and all(isinstance(r, str) and r for r in score["reasons"])


def test_pricing_for_unknown_company_does_not_count():
    verified = comps(4) + [claim("pricing", "Zoom charges $13 a month"), claim("pricing", "ChatGPT Go is free")]
    score = build_score(verified, memory_checked=True)
    pricing_item = next(i for i in score["items"] if i["key"] == "pricing")
    assert pricing_item["found"] == 0
    assert pricing_item["passed"] is False


def test_matched_pricing_keeps_only_known_competitors():
    verified = comps(2) + [claim("pricing", "Alpha charges $5"), claim("pricing", "Zoom charges $9")]
    assert [c["text"] for c in matched_pricing(verified)] == ["Alpha charges $5"]