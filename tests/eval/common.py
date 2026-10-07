import json
from pathlib import Path

from app.scoring import VERDICT_CAUTION, VERDICT_PROMISING, VERDICT_RISKY, VERDICT_UNCLEAR

EVAL_DIR = Path(__file__).resolve().parent
CASES_FILE = EVAL_DIR / "critic_cases.json"
IDEAS_FILE = EVAL_DIR / "idea_cases.json"
RESULTS_DIR = EVAL_DIR / "results"

VERDICT_BY_KEY = {
    "Promising": VERDICT_PROMISING,
    "Caution": VERDICT_CAUTION,
    "Risky": VERDICT_RISKY,
    "Unclear": VERDICT_UNCLEAR,
}
KEY_BY_VERDICT = {verdict: key for key, verdict in VERDICT_BY_KEY.items()}

# The idea the critic cases are judged against
PROFILE = {
    "name": "Study Buddy Groups",
    "problem": "College students in India struggle to find reliable study partners for exams.",
    "target_customer": "College students in India",
    "solution": ("An app that matches students into small study groups for exam preparation, "
                 "with a shared study planner and weekly mock quizzes."),
    "geography": "India",
    "category": "edtech",
}


def load_cases() -> list:
    return json.loads(CASES_FILE.read_text(encoding="utf-8"))


def load_ideas() -> list:
    return json.loads(IDEAS_FILE.read_text(encoding="utf-8"))


def build_inputs(case: dict):
    """Turn one test case into the inputs of check_claim: (claim, sources, past_notes)."""
    sources = [{"title": "Case source", "url": "https://example.com/case",
                "content": case.get("source_text", "")}]
    claim = {
        "text": case["claim"],
        "category": case["category"],
        "source_ids": list(case.get("source_ids", [1])),
        "from_notes": bool(case.get("note_quote")),
    }
    if case.get("note_quote"):
        claim["note_quote"] = case["note_quote"]
    return claim, sources, list(case.get("past_notes", []))


def ratio(part: int, whole: int) -> str:
    if not whole:
        return f"{part}/{whole}"
    return f"{part}/{whole} ({round(100 * part / whole)}%)"


def summarize_critic(rows: list) -> dict:
    """rows: dicts with id, expected, got, layer. Only 'verified' and 'dropped' results are scored."""
    scored = [r for r in rows if r["got"] in ("verified", "dropped")]
    good = [r for r in scored if r["expected"] == "verified"]
    bad = [r for r in scored if r["expected"] == "dropped"]
    by_layer = {}
    for layer in ("code", "llm"):
        part = [r for r in scored if r["layer"] == layer]
        by_layer[layer] = (sum(r["got"] == r["expected"] for r in part), len(part))
    return {
        "scored": len(scored),
        "correct": sum(r["got"] == r["expected"] for r in scored),
        "bad_caught": (sum(r["got"] == "dropped" for r in bad), len(bad)),
        "good_kept": (sum(r["got"] == "verified" for r in good), len(good)),
        "unsafe_passes": [r["id"] for r in bad if r["got"] == "verified"],
        "false_drops": [r["id"] for r in good if r["got"] == "dropped"],
        "by_layer": by_layer,
    }


def summarize_verdicts(rows: list) -> dict:
    """rows: dicts with id, verdict_key, acceptable, must_not."""
    return {
        "total": len(rows),
        "within_range": [r["id"] for r in rows if r["verdict_key"] in r["acceptable"]],
        "overconfident": [r["id"] for r in rows if r["verdict_key"] in r["must_not"]],
        "unclear": [r["id"] for r in rows if r["verdict_key"] == "Unclear"],
    }