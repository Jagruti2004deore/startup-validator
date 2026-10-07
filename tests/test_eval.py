import pytest

import app.agents.critic as critic_mod
from app.agents.critic import check_claim
from app.models import ClaimCheck
from tests.eval.common import (
    PROFILE, VERDICT_BY_KEY, build_inputs, load_cases, load_ideas,
    summarize_critic, summarize_verdicts,
)

CASES = load_cases()
CODE_CASES = [c for c in CASES if c["layer"] == "code"]
GOOD_LLM_CASES = [c for c in CASES if c["layer"] == "llm" and c["expected"] == "verified"]


def reason_code(reason) -> str:
    return str(reason or "").split(":")[0].strip()


# ---------- the data files ----------
def test_critic_cases_are_well_formed():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids)) >= 20
    for c in CASES:
        assert c["expected"] in ("verified", "dropped")
        assert c["layer"] in ("code", "llm")
        assert c["claim"] and c["category"]
        if c["expected"] == "dropped":
            assert c["expected_reasons"], c["id"]


def test_idea_cases_are_well_formed():
    ideas = load_ideas()
    assert len({i["id"] for i in ideas}) == len(ideas)
    for i in ideas:
        assert i["group"] in ("crowded", "niche", "obscure")
        assert len(i["idea"]) >= 15
        assert set(i["acceptable"]) <= set(VERDICT_BY_KEY)
        assert set(i["must_not"]) <= set(VERDICT_BY_KEY)
        assert not set(i["acceptable"]) & set(i["must_not"])


# ---------- critic rules, no LLM ----------
@pytest.fixture
def no_llm(monkeypatch):
    def refuse(*args, **kwargs):
        raise RuntimeError("the LLM must not be called")
    monkeypatch.setattr(critic_mod, "ask_structured", refuse)


@pytest.mark.parametrize("case", CODE_CASES, ids=lambda c: c["id"])
def test_cases_decided_by_code_rules(case, no_llm):
    claim, sources, notes = build_inputs(case)
    ok, bad = check_claim(claim, sources, notes, PROFILE)
    if case["expected"] == "verified":
        assert ok is not None, bad
    else:
        assert ok is None
        assert reason_code(bad["reason"]) in case["expected_reasons"], bad["reason"]


# ---------- good claims must not be killed by the code rules ----------
@pytest.mark.parametrize("case", GOOD_LLM_CASES, ids=lambda c: c["id"])
def test_good_claims_survive_the_code_checks(case, monkeypatch):
    def supportive(llm, prompt, model, tries=3):
        return ClaimCheck(
            supported=True,
            evidence_quote=case["source_text"],
            best_category=case.get("true_category", case["category"]),
            reason="ok",
        )

    monkeypatch.setattr(critic_mod, "ask_structured", supportive)
    monkeypatch.setattr(critic_mod, "get_llm", lambda: None)
    claim, sources, notes = build_inputs(case)
    ok, bad = check_claim(claim, sources, notes, PROFILE)
    assert ok is not None, bad


# ---------- the summaries ----------
def test_critic_summary_counts():
    rows = [
        {"id": "a", "expected": "verified", "got": "verified", "layer": "llm"},
        {"id": "b", "expected": "verified", "got": "dropped", "layer": "llm"},
        {"id": "c", "expected": "dropped", "got": "dropped", "layer": "code"},
        {"id": "d", "expected": "dropped", "got": "verified", "layer": "llm"},
        {"id": "e", "expected": "dropped", "got": "skipped (needs LLM)", "layer": "llm"},
    ]
    s = summarize_critic(rows)
    assert s["scored"] == 4 and s["correct"] == 2
    assert s["bad_caught"] == (1, 2) and s["good_kept"] == (1, 2)
    assert s["unsafe_passes"] == ["d"] and s["false_drops"] == ["b"]
    assert s["by_layer"] == {"code": (1, 1), "llm": (1, 3)}


def test_verdict_summary_counts():
    rows = [
        {"id": "x", "verdict_key": "Promising", "acceptable": ["Promising", "Caution"], "must_not": ["Risky"]},
        {"id": "y", "verdict_key": "Promising", "acceptable": ["Unclear"], "must_not": ["Promising"]},
        {"id": "z", "verdict_key": "Unclear", "acceptable": ["Unclear"], "must_not": ["Promising"]},
    ]
    s = summarize_verdicts(rows)
    assert s["within_range"] == ["x", "z"]
    assert s["overconfident"] == ["y"]
    assert s["unclear"] == ["z"]