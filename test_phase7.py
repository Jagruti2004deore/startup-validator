from app.scoring import build_score, format_score


def comps(names):
    return [{"category": "competitor", "text": f"{n} offers a study tool"} for n in names]


def c(category):
    return {"category": category, "text": f"{category} fact"}


scenarios = {
    "A. Strong evidence, a gap, a modest market": (
        comps(["Alpha", "Beta", "Gamma", "Delta"])
        + [c("pricing"), c("pricing"), c("demand_signal"), c("market_size"),
           c("recent_activity"), c("failure_or_risk"), c("differentiation_gap")],
        True,
    ),
    "B. Very little verified evidence": (
        comps(["Alpha", "Beta"]) + [c("market_size")],
        True,
    ),
    "C. Crowded market, no gap": (
        comps(["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta"])
        + [c("pricing"), c("pricing"), c("demand_signal"), c("market_size")],
        True,
    ),
    "D. Promising, but your own past note conflicts": (
        comps(["Alpha", "Beta", "Gamma", "Delta"])
        + [c("pricing"), c("pricing"), c("demand_signal"), c("market_size"),
           c("recent_activity"), c("failure_or_risk"), c("differentiation_gap"),
           c("conflict_with_past_notes")],
        True,
    ),
}

for title, (verified, memory_ok) in scenarios.items():
    print(f"\n=== {title} ===")
    print(format_score(build_score(verified, memory_ok)))