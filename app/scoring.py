import re
from collections import Counter

from app import db
from app.config import (
    MIN_VERIFIED, MIN_EVIDENCE_FOR_VERDICT, CROWDED_MEDIUM, CROWDED_HIGH,
)
from app.state import ValidatorState

VERDICT_UNCLEAR = "Unclear: not enough verified evidence"
VERDICT_RISKY = "Risky"
VERDICT_PROMISING = "Promising"
VERDICT_CAUTION = "Proceed with caution"

# (key, label, claim category). The number needed comes from MIN_VERIFIED in config.
EVIDENCE_ITEMS = [
    ("competitors", "Distinct direct competitors", "competitor"),
    ("pricing", "Pricing found for verified competitors", "pricing"),
    ("demand", "Evidence of customer pain or demand", "demand_signal"),
    ("market_size", "Market size or growth figure", "market_size"),
    ("recent_activity", "Recent activity in the space", "recent_activity"),
    ("failure_or_risk", "A documented failure or risk", "failure_or_risk"),
]
TOTAL_ITEMS = len(EVIDENCE_ITEMS) + 2  # plus the differentiation gap and the memory check

# The company name at the start of a claim, for example "Kahoot+ Study"
LEAD_NAME_RE = re.compile(r"^((?:[A-Z][\w+&'\-]*\s?){1,3})")


def _tokens(text: str) -> list:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def competitor_key(text: str) -> str:
    """A rough company name for a competitor claim, so one company counts once."""
    match = LEAD_NAME_RE.match((text or "").strip())
    key = match.group(1).strip().lower() if match else ""
    if not key:
        key = " ".join((text or "").lower().split()[:2])
    return key


def count_competitors(verified: list) -> int:
    """Number of distinct competitors among the verified claims."""
    return len({
        competitor_key(c.get("text", ""))
        for c in verified if c.get("category") == "competitor"
    })


def matched_pricing(verified: list) -> list:
    """Pricing claims that name a verified competitor. Other pricing claims do not count."""
    keys = []
    for c in verified:
        if c.get("category") == "competitor":
            tokens = _tokens(competitor_key(c.get("text", "")))[:2]
            if tokens:
                keys.append(tokens)
    result = []
    for c in verified:
        if c.get("category") != "pricing":
            continue
        words = set(_tokens(c.get("text", "")))
        if any(all(tok in words for tok in key) for key in keys):
            result.append(c)
    return result


def crowdedness(n_competitors: int) -> str:
    if n_competitors == 0:
        return "unknown"
    if n_competitors >= CROWDED_HIGH:
        return "high"
    if n_competitors >= CROWDED_MEDIUM:
        return "medium"
    return "low"


def decide_verdict(points, crowd, has_gap, has_demand, has_conflict):
    """Returns (verdict, rule_description). The order of the rules matters."""
    if points < MIN_EVIDENCE_FOR_VERDICT:
        return VERDICT_UNCLEAR, (
            f"fewer than {MIN_EVIDENCE_FOR_VERDICT} of {TOTAL_ITEMS} checklist items were verified"
        )
    if crowd == "high" and not has_gap:
        return VERDICT_RISKY, "crowded market and no verified differentiation gap"
    if has_gap and has_demand and crowd != "high" and not has_conflict:
        return VERDICT_PROMISING, (
            "verified differentiation gap and verified demand, in a market that is not crowded"
        )

    blockers = []
    if not has_gap:
        blockers.append("no verified differentiation gap")
    if not has_demand:
        blockers.append("no verified demand evidence")
    if crowd == "high":
        blockers.append("a crowded market")
    if has_conflict:
        blockers.append("your past notes conflict with this idea")
    return VERDICT_CAUTION, "not Promising because of: " + ", ".join(blockers)


def build_score(verified: list, memory_checked: bool) -> dict:
    """Checklist and verdict from verified claims. Plain rules, no LLM."""
    counts = Counter(c.get("category") for c in verified)
    n_comp = count_competitors(verified)
    counts["competitor"] = n_comp
    counts["pricing"] = len(matched_pricing(verified))  # only prices of verified competitors

    items = []
    for key, label, category in EVIDENCE_ITEMS:
        need = MIN_VERIFIED[category]
        found = counts[category]
        items.append({"key": key, "label": label, "needed": need,
                      "found": found, "passed": found >= need})

    has_gap = counts["differentiation_gap"] > 0
    items.append({"key": "differentiation_gap",
                  "label": "A differentiation gap was identified",
                  "needed": 1, "found": counts["differentiation_gap"], "passed": has_gap})
    items.append({"key": "memory", "label": "Your past notes were checked",
                  "needed": 1, "found": 1 if memory_checked else 0, "passed": memory_checked})

    points = sum(1 for i in items if i["passed"])
    crowd = crowdedness(n_comp)
    has_demand = counts["demand_signal"] >= MIN_VERIFIED["demand_signal"]
    has_conflict = counts["conflict_with_past_notes"] > 0

    verdict, rule = decide_verdict(points, crowd, has_gap, has_demand, has_conflict)

    reasons = [f"Evidence score: {points} of {TOTAL_ITEMS} checklist items verified."]
    reasons.append(
        f"Market crowdedness: {crowd} ({n_comp} distinct competitor(s) verified; "
        "the real number can only be higher)."
    )
    missing = [i["label"] for i in items if not i["passed"]]
    if missing:
        reasons.append("Not verified: " + "; ".join(missing) + ".")
    if has_conflict:
        reasons.append("Your past notes conflict with, or repeat a past rejection of, this idea.")
    reasons.append(f"Rule applied: {rule}.")

    return {
        "items": items,
        "evidence_score": points,
        "max_score": TOTAL_ITEMS,
        "competitors_found": n_comp,
        "crowdedness": crowd,
        "has_gap": has_gap,
        "has_demand": has_demand,
        "has_conflict": has_conflict,
        "verdict": verdict,
        "reasons": reasons,
    }


def format_score(score: dict) -> str:
    """Plain-text view of a score, for the terminal."""
    lines = []
    for i in score["items"]:
        mark = "[x]" if i["passed"] else "[ ]"
        lines.append(f"  {mark} {i['label']} ({i['found']}/{i['needed']})")
    lines.append(f"  Evidence score: {score['evidence_score']}/{score['max_score']}")
    lines.append(f"  Crowdedness: {score['crowdedness']} ({score['competitors_found']} competitors)")
    lines.append(f"  VERDICT: {score['verdict']}")
    for reason in score["reasons"]:
        lines.append(f"    - {reason}")
    return "\n".join(lines)


def score_node(state: ValidatorState) -> dict:
    """The graph node: drop pricing for non-competitors, score the rest, save the verdict."""
    verified = state["verified"]
    keep_ids = {id(c) for c in matched_pricing(verified)}
    unmatched_ids = {
        id(c) for c in verified
        if c.get("category") == "pricing" and id(c) not in keep_ids
    }
    usable = [c for c in verified if id(c) not in unmatched_ids]
    moved = [
        dict(c, reason="pricing_for_unverified_competitor")
        for c in verified if id(c) in unmatched_ids
    ]
    dropped = list(state["dropped"]) + moved

    score = build_score(usable, state.get("memory_checked", False))
    db.save_claims(state["run_id"], usable, dropped)
    db.update_run(
        state["run_id"],
        verdict=score["verdict"],
        evidence_score=score["evidence_score"],
    )
    db.add_event(
        state["run_id"], "scoring",
        f"Evidence score {score['evidence_score']}/{score['max_score']}. Verdict: {score['verdict']}",
    )
    return {"score": score, "verdict": score["verdict"], "verified": usable, "dropped": dropped}