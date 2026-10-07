from app.agents.reporter import build_report, validate_summary
from app.scoring import build_score
from app.utils import repair_spacing

SOURCES = [
    {"title": f"Source {i}", "url": f"https://example.com/{i}", "content": ""}
    for i in range(1, 7)
]


def make_state():
    verified = [
        {"category": "competitor", "text": "Alpha offers study groups", "source_ids": [5]},
        {"category": "competitor", "text": "Beta offers study rooms", "source_ids": [3]},
        {"category": "competitor", "text": "Gamma offers quizzes", "source_ids": [3]},
        {"category": "pricing", "text": "Alpha charges $5 a month", "source_ids": [5]},
        {"category": "pricing", "text": "Beta charges $7 a month", "source_ids": [3]},
        {"category": "market_size", "text": "The market is USD 4.60 Billion", "source_ids": [2]},
        {"category": "market_size", "text": "The market is USD 7.5 billion", "source_ids": [6]},
        {"category": "demand_signal", "text": "Students report studying alone", "source_ids": [1]},
        {"category": "differentiation_gap",
         "text": "Among the competitors found, none mention a shared planner.",
         "source_ids": [3, 5], "derived": True},
    ]
    dropped = [{"category": "pricing", "text": "Alpha charges $49",
                "reason": "number_not_in_source: 49", "source_ids": [5]}]
    return {
        "profile": {"name": "Study Buddy"},
        "idea_text": "A study app for students.",
        "verified": verified,
        "dropped": dropped,
        "sources": SOURCES,
        "score": build_score(verified, memory_checked=True),
        "past_notes": [],
        "memory_checked": True,
    }


SUMMARY = "Alpha is a rival [C1]. Beta is one too [C2]."
HAYSTACK = "C1: Alpha offers study groups C2: Alpha charges $5 a month 7 8"


# ---------- the report ----------
def test_citations_follow_first_appearance():
    report = build_report(make_state(), SUMMARY)
    assert "Alpha is a rival [1]." in report
    assert "Beta is one too [2]." in report
    assert "[1] Source 5 - https://example.com/5" in report
    assert "[2] Source 3 - https://example.com/3" in report


def test_only_cited_sources_are_listed():
    report = build_report(make_state(), SUMMARY)
    assert "https://example.com/4" not in report


def test_empty_sections_say_so():
    report = build_report(make_state(), SUMMARY)
    assert "_No verified evidence found._" in report


def test_market_disagreement_is_flagged():
    report = build_report(make_state(), SUMMARY)
    assert "do not agree" in report


def test_removed_claims_are_explained():
    report = build_report(make_state(), SUMMARY)
    assert "A number in the claim was not in the source" in report


def test_gap_is_labeled_as_analysis():
    report = build_report(make_state(), SUMMARY)
    assert "Not a statement from a source" in report


def test_verdict_is_in_the_report():
    state = make_state()
    report = build_report(state, SUMMARY)
    assert f"**Verdict: {state['score']['verdict']}**" in report


# ---------- the summary checks ----------
def test_good_summary_passes():
    good = "The idea looks promising because a gap was found [C1]. Alpha charges $5 a month [C2]."
    assert validate_summary(good, 3, "Promising", HAYSTACK) is None


def test_uncited_sentence_is_rejected():
    text = "The idea looks promising [C1]. This sentence has no citation."
    assert validate_summary(text, 3, "Promising", HAYSTACK) == "uncited_sentence"


def test_made_up_claim_number_is_rejected():
    text = "The idea looks promising [C9]. Alpha charges $5 a month [C2]."
    assert validate_summary(text, 3, "Promising", HAYSTACK) == "bad_citation"


def test_invented_number_is_rejected():
    text = "The idea looks promising [C1]. Alpha charges $49 a month [C2]."
    assert validate_summary(text, 3, "Promising", HAYSTACK).startswith("number_not_in_facts")


def test_wrong_verdict_is_rejected():
    text = "Alpha charges $5 a month [C1]. Nothing else to add [C2]."
    assert validate_summary(text, 3, "Promising", HAYSTACK) == "verdict_not_stated"


def test_one_sentence_is_too_short():
    assert validate_summary("Looks promising [C1].", 3, "Promising", HAYSTACK) == "length"


# ---------- spacing repair ----------
def test_spacing_repair():
    assert repair_spacing("USD 3.63Billion in2026") == "USD 3.63 Billion in 2026"
    assert repair_spacing("grew,then fell") == "grew, then fell"


def test_spacing_repair_leaves_good_text_alone():
    text = "Raised $5M in 2026 at 27.94% CAGR, per Wh/kg data"
    assert repair_spacing(text) == text

def test_sentence_about_missing_evidence_needs_no_citation():
    text = "The idea looks promising because a gap was found [C1]. Customer demand could not be verified."
    assert validate_summary(text, 3, "Promising", HAYSTACK) is None