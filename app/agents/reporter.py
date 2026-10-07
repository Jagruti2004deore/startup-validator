import re
from collections import Counter

from app import db
from app.agents.critic import numbers_missing
from app.llm_utils import ask_text, get_llm
from app.prompts import SUMMARY_PROMPT
from app.scoring import VERDICT_UNCLEAR, VERDICT_RISKY, VERDICT_PROMISING, VERDICT_CAUTION
from app.state import ValidatorState
from app.utils import clean_text, repair_spacing, today_note

SECTIONS = [
    ("competitor", "Competitors"),
    ("pricing", "Pricing"),
    ("market_size", "Market size"),
    ("demand_signal", "Customer demand"),
    ("recent_activity", "Recent activity"),
    ("failure_or_risk", "Failures and risks"),
]
CATEGORY_LABEL = {
    **dict(SECTIONS),
    "differentiation_gap": "analysis based on verified competitors",
    "conflict_with_past_notes": "from the founder's past notes",
}
VERDICT_WORD = {
    VERDICT_UNCLEAR: "unclear",
    VERDICT_RISKY: "risky",
    VERDICT_PROMISING: "promising",
    VERDICT_CAUTION: "caution",
}
REASON_LABELS = {
    "number_not_in_source": "A number in the claim was not in the source",
    "name_not_in_source": "A company name in the claim was not in the source",
    "source_number_does_not_exist": "The claim cited a source that does not exist",
    "no_source_cited": "The claim cited no source",
    "not_supported_by_source": "The source did not support the claim",
    "quote_not_found_in_source": "The supporting quote was not found in the source",
    "not_relevant_to_idea": "True, but not useful evidence for this idea",
    "not_a_market_figure": "Not a market size or growth figure",
    "pricing_for_unverified_competitor": "Pricing for a company not verified as a competitor",
    "note_quote_not_found": "The quoted note text was not found in your notes",
    "feature_already_offered": "The gap feature is already offered by a competitor",
    "check_failed": "The check could not be completed",
}
MAX_FACTS = 25  # the summary prompt lists at most this many verified claims

# a sentence that only says something could not be verified needs no citation
ABSENCE_RE = re.compile(
    r"\b(?:could not|cannot|can't|not|no|nothing|unable)\b[^.\[\]]*\bverif(?:ied|y)\b|\bunverified\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Citations: numbered by first appearance, so the report reads [1], [2], [3]...
# ---------------------------------------------------------------------------

class Citer:
    def __init__(self, sources: list):
        self.sources = sources
        self.order = []    # original source numbers, in order of first use
        self.number = {}   # original source number -> display number

    def cite(self, claim: dict) -> str:
        parts = []
        for i in claim.get("source_ids", []):
            if not (1 <= i <= len(self.sources)):
                continue
            if i not in self.number:
                self.order.append(i)
                self.number[i] = len(self.order)
            parts.append(f"[{self.number[i]}]")
        return "".join(parts)

    def sources_section(self) -> list:
        if not self.order:
            return ["_No sources were cited._"]
        lines = []
        for original in self.order:
            s = self.sources[original - 1]
            title = repair_spacing(clean_text(s.get("title") or "Untitled"))
            lines.append(f"[{self.number[original]}] {title} - {s.get('url', '')}  ")
        return lines


def _reason_label(reason) -> str:
    code = str(reason).split(":")[0].strip()
    return REASON_LABELS.get(code, code.replace("_", " ") or "other")


# ---------------------------------------------------------------------------
# The summary: written by the LLM, then checked in code
# ---------------------------------------------------------------------------

def facts_for_prompt(claims: list) -> str:
    lines = []
    for n, c in enumerate(claims[:MAX_FACTS], start=1):
        label = CATEGORY_LABEL.get(c["category"], c["category"])
        lines.append(f"C{n}: ({label}) {repair_spacing(c['text'])}")
    return "\n".join(lines)


def validate_summary(summary: str, n_claims: int, verdict: str, haystack: str):
    """Returns None if the summary is acceptable, otherwise the reason it was rejected."""
    ids = [int(n) for n in re.findall(r"\[C(\d+)\]", summary)]
    if not ids or any(n < 1 or n > n_claims for n in ids):
        return "bad_citation"
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", summary.strip()) if s]
    if not 2 <= len(sentences) <= 6:
        return "length"
    if any(not re.search(r"\[C\d+\]", s) and not ABSENCE_RE.search(s) for s in sentences):
        return "uncited_sentence"
    plain = re.sub(r"\[C\d+\]", "", summary)
    missing = numbers_missing(plain, haystack)
    if missing:
        return "number_not_in_facts: " + ", ".join(missing)
    if VERDICT_WORD.get(verdict, "") not in sentences[0].lower():
        return "verdict_not_stated"
    return None


def fallback_summary(state: dict) -> str:
    """A summary built from fixed templates, used when the LLM summary is rejected."""
    score, claims = state["score"], state["verified"]

    def first(category):
        for n, c in enumerate(claims[:MAX_FACTS], start=1):
            if c["category"] == category:
                return n
        return None

    parts = [
        f"The rule-based verdict is {score['verdict']}, with "
        f"{score['evidence_score']} of {score['max_score']} checklist items verified."
    ]
    comp = first("competitor")
    sentence = (
        f"Verified competitors: {score['competitors_found']} "
        f"(market crowdedness: {score['crowdedness']})"
    )
    parts.append(sentence + (f" [C{comp}]." if comp else "."))

    gap = first("differentiation_gap")
    if gap:
        text = repair_spacing(claims[gap - 1]["text"]).rstrip(" .")
        parts.append(f"{text} [C{gap}].")
    else:
        parts.append("No differentiation gap could be verified.")
    parts.append("Everything that could not be verified is listed below.")
    return " ".join(parts)


def make_summary(state: dict):
    """Returns (summary_text, 'llm' or 'template')."""
    claims, score = state["verified"], state["score"]
    if not claims:
        return fallback_summary(state), "template"

    facts = facts_for_prompt(claims)
    missing = "; ".join(i["label"] for i in score["items"] if not i["passed"]) or "nothing major"
    prompt = today_note() + SUMMARY_PROMPT.format(
        name=state["profile"].get("name", "the idea"),
        solution=state["profile"].get("solution", ""),
        verdict=score["verdict"],
        points=score["evidence_score"],
        max_points=score["max_score"],
        crowd=score["crowdedness"],
        facts=facts,
        missing=missing,
    )
    try:
        text = " ".join(clean_text(ask_text(get_llm(), prompt)).split())
    except Exception as e:
        print(f"  (summary writer failed: {e})")
        return fallback_summary(state), "template"

    extras = (
        f"{score['evidence_score']} {score['max_score']} {score['competitors_found']} "
        f"{len(claims)} {len(state['dropped'])} {len(state['sources'])}"
    )
    problem = validate_summary(text, min(len(claims), MAX_FACTS), score["verdict"], facts + " " + extras)
    if problem:
        print(f"  (summary rejected: {problem}; using the template summary)")
        return fallback_summary(state), "template"
    return text, "llm"


# ---------------------------------------------------------------------------
# The report itself (plain Python)
# ---------------------------------------------------------------------------

def build_report(state: dict, summary_raw: str) -> str:
    profile, score = state["profile"], state["score"]
    claims, dropped = state["verified"], state["dropped"]
    citer = Citer(state["sources"])

    def convert(match):
        n = int(match.group(1))
        if not (1 <= n <= len(claims)):
            return ""
        claim = claims[n - 1]
        if claim.get("from_notes"):
            return "(your notes)"
        return citer.cite(claim)

    summary = re.sub(r"\[C(\d+)\]", convert, summary_raw)

    out = []
    name = repair_spacing(profile.get("name") or "Startup idea")
    out.append(f"# {name}: startup idea validation")
    out.append("")
    out.append(f"> **Verdict: {score['verdict']}**  ")
    out.append(
        f"> Evidence score: {score['evidence_score']} of {score['max_score']} | "
        f"Market crowdedness: {score['crowdedness']} "
        f"({score['competitors_found']} verified competitors)"
    )
    out.append("")
    out.append(f"**Idea:** {state['idea_text'].strip()}")
    out.append("")

    out.append("## Summary")
    out.append(summary)
    out.append("")

    out.append("## Why this verdict")
    for reason in score["reasons"]:
        out.append(f"- {reason}")
    out.append("")

    out.append("## Evidence checklist")
    out.append("| Checklist item | Verified | Needed | Result |")
    out.append("|---|---|---|---|")
    for item in score["items"]:
        result = "Yes" if item["passed"] else "No"
        out.append(f"| {item['label']} | {item['found']} | {item['needed']} | {result} |")
    out.append("")

    out.append("## Key findings")
    by_category = {}
    for c in claims:
        by_category.setdefault(c["category"], []).append(c)

    for category, title in SECTIONS:
        out.append(f"### {title}")
        items = by_category.get(category, [])
        if not items:
            out.append("_No verified evidence found._")
        for c in items:
            out.append(f"- {repair_spacing(c['text'])} {citer.cite(c)}".rstrip())
        if category == "market_size" and len(items) >= 2:
            out.append("_These figures come from different publishers and do not agree. "
                       "Treat them as a range, not a single number._")
        out.append("")

    out.append("### Differentiation gap")
    gaps = by_category.get("differentiation_gap", [])
    if not gaps:
        out.append("_No differentiation gap could be verified._")
    for c in gaps:
        out.append(f"- {repair_spacing(c['text'])} {citer.cite(c)}".rstrip())
    if gaps:
        out.append("_Analysis based on the verified competitor facts above. "
                   "Not a statement from a source._")
    out.append("")

    out.append("### Your past notes")
    note_claims = by_category.get("conflict_with_past_notes", [])
    for c in note_claims:
        out.append(f"- {repair_spacing(c['text'])} (your note: \"{c.get('note_quote', '')}\")")
    if not note_claims:
        if not state.get("memory_checked"):
            out.append("_Your notes could not be searched for this run._")
        elif state.get("past_notes"):
            out.append(f"_Found {len(state['past_notes'])} similar past note(s); "
                       "none conflicts with this idea._")
        else:
            out.append("_No similar past notes were found._")
    out.append("")

    out.append("## What could not be verified")
    failed = [i for i in score["items"] if not i["passed"]]
    if not failed:
        out.append("_Every checklist item was verified._")
    for i in failed:
        out.append(f"- {i['label']} ({i['found']} of {i['needed']} verified)")
    out.append("")

    out.append("## What the critic removed")
    if not dropped:
        out.append("_No claims were removed._")
    else:
        out.append(f"{len(dropped)} claim(s) were removed because they failed a check:")
        out.append("")
        for reason, n in Counter(_reason_label(d.get("reason", "")) for d in dropped).most_common():
            out.append(f"- {reason}: {n}")
        out.append("")
        out.append("Examples:")
        for d in dropped[:5]:
            text = repair_spacing(d["text"])
            text = text if len(text) <= 110 else text[:107] + "..."
            out.append(f"- \"{text}\" ({_reason_label(d.get('reason', ''))})")
    out.append("")

    out.append("## How to read this report")
    out.append("- Every finding was checked in code against the text of its source. "
               "Claims that failed were removed.")
    out.append("- The agent read search-result snippets, not full web pages, "
               "so details can be missing.")
    out.append("- The verdict comes from fixed rules, not from the language model. "
               "It is decision support, not a prediction of success.")
    out.append("- The competitor count includes only verified competitors, "
               "so the real market can be more crowded.")
    out.append("")

    out.append("## Sources")
    out.extend(citer.sources_section())
    return "\n".join(out)


def report_node(state: ValidatorState) -> dict:
    summary_raw, used = make_summary(state)
    report = build_report(state, summary_raw)
    label = "AI-written" if used == "llm" else "template"
    db.update_run(state["run_id"], report_md=report)
    db.add_event(state["run_id"], "reporter", f"Wrote the report ({label} summary)")
    return {"report": report}