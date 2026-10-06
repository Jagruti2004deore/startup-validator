import re
from collections import Counter

from app import db
from app.config import MIN_VERIFIED, MAX_SOURCES_PER_CLAIM
from app.llm_utils import ask_structured, get_llm
from app.models import ClaimCheck, GapStatement
from app.prompts import CRITIC_PROMPT, GAP_PROMPT
from app.state import ValidatorState
from app.utils import clean_text

# ---------------------------------------------------------------------------
# Rule helpers (plain Python, no LLM). Tested in tests/test_critic_rules.py
# ---------------------------------------------------------------------------

NUMBER_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?!\d)(?:\.\d+)?|\d+(?:\.\d+)?")
NAME_RE = re.compile(r"\b[A-Z][A-Za-z0-9+&'\-]{2,}")
UNIT_AFTER_RE = re.compile(
    r"\s*(?:%|percent\b|million\b|billion\b|trillion\b|crore\b|lakh\b|thousand\b|[kmb]\b)",
    re.IGNORECASE,
)

# Capitalised words that are not company or product names
NAME_STOP = {
    "the", "this", "that", "these", "those", "its", "their", "there", "nearly",
    "over", "around", "about", "more", "most", "many", "some", "india", "indian",
    "indians", "usd", "inr", "cagr", "edtech", "app", "apps", "higher", "education",
    "market", "markets", "students", "student", "college", "colleges", "university",
    "universities", "school", "schools", "billion", "million", "trillion",
    "according", "based", "new", "recent", "top", "best", "free", "online", "global",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
}
GENERIC_WORDS = {"that", "with", "from", "their", "which", "this", "apps", "based", "using"}


def norm(text: str) -> str:
    """Lowercase, straighten quotes and dashes, collapse spaces."""
    text = (text or "").lower()
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " ")):
        text = text.replace(a, b)
    return " ".join(text.split())


def _alnum(text: str) -> str:
    """Letters and digits only. Ignores spacing and punctuation differences."""
    return re.sub(r"[^a-z0-9]", "", norm(text))


def _squash(text: str) -> str:
    """Remove thousands commas so 1,000,000 becomes 1000000."""
    return re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)


def numbers_in(text: str) -> set:
    """Numbers in a claim. One-digit numbers count only with a unit or currency."""
    found = set()
    for m in NUMBER_RE.finditer(text):
        tok = m.group().replace(",", "")
        if "." not in tok and len(tok) < 2:
            before = text[max(0, m.start() - 4):m.start()]
            after = text[m.end():m.end() + 12]
            has_unit = (
                bool(UNIT_AFTER_RE.match(after))
                or bool(re.search(r"[$\u20b9\u20ac\u00a3]\s*$", before))
                or before.strip().upper().endswith(("USD", "INR"))
            )
            if not has_unit:
                continue
        found.add(tok)
    return found


def _has_number(tok: str, haystack: str) -> bool:
    pattern = r"(?<!\d)(?<!\d\.)" + re.escape(tok) + r"(?!\d)(?!\.\d)"
    return re.search(pattern, haystack) is not None


def numbers_missing(claim_text: str, haystack: str) -> list:
    """Numbers in the claim that do not appear in the source text."""
    hay = _squash(haystack)
    missing = []
    for tok in sorted(numbers_in(claim_text)):
        variants = [tok]
        if tok.endswith(".0"):
            variants.append(tok[:-2])
        if not any(_has_number(v, hay) for v in variants):
            missing.append(tok)
    return missing


def names_in(claim_text: str) -> list:
    names = []
    for m in NAME_RE.findall(claim_text):
        tok = m.rstrip("+&'-")
        if len(tok) < 3 or tok.lower() in NAME_STOP or tok in names:
            continue
        names.append(tok)
    return names


def names_missing(claim_text: str, haystack: str) -> list:
    """Company or product names in the claim that do not appear in the source text."""
    hay_words = norm(haystack)
    hay_flat = _alnum(haystack)
    missing = []
    for name in names_in(claim_text):
        flat = _alnum(name)
        if len(flat) <= 4:
            # short names (like YPT) must match as whole words, or "ypt" would match "encrypted"
            found = re.search(r"\b" + re.escape(name.lower()) + r"\b", hay_words) is not None
        else:
            found = flat in hay_flat   # ignores spacing, hyphens and slashes
        if not found:
            missing.append(name)
    return missing


def quote_in_source(quote: str, haystack: str) -> bool:
    """True only if the quote is a real passage of the source (spacing differences are ignored)."""
    q = norm(quote).strip(" .\"'")
    if len(q) < 20 or "..." in q:
        return False
    return _alnum(q) in _alnum(haystack)


def compute_gaps(verified: list) -> list:
    """Research angles that still lack enough verified claims."""
    counts = Counter(c["category"] for c in verified)
    return [angle for angle, need in MIN_VERIFIED.items() if counts.get(angle, 0) < need]


# ---------------------------------------------------------------------------
# Checking one claim
# ---------------------------------------------------------------------------

def _drop(claim: dict, reason: str):
    dropped = dict(claim)
    dropped["reason"] = reason
    return None, dropped


def _source_text(sources: list, ids: list) -> str:
    return "\n\n".join(f"{sources[i - 1]['title']}\n{sources[i - 1]['content']}" for i in ids)


def check_claim(claim: dict, sources: list, past_notes: list, profile: dict):
    """Returns (verified_claim, None) or (None, dropped_claim_with_reason)."""
    c = dict(claim)

    # Claims about the founder's own notes: the quote must be in a real note
    if c.get("from_notes"):
        quote = c.get("note_quote", "")
        if any(quote_in_source(quote, n) for n in past_notes):
            c["evidence_quote"] = quote
            return c, None
        return _drop(c, "note_quote_not_found")

    # Check 1: source numbers
    ids = sorted({int(i) for i in c.get("source_ids", [])})
    if not ids:
        return _drop(c, "no_source_cited")
    if any(i < 1 or i > len(sources) for i in ids):
        return _drop(c, "source_number_does_not_exist")
    ids = ids[:MAX_SOURCES_PER_CLAIM]
    c["source_ids"] = ids
    haystack = _source_text(sources, ids)

    # Check 2: numbers
    missing = numbers_missing(c["text"], haystack)
    if missing:
        return _drop(c, f"number_not_in_source: {', '.join(missing)}")

    # Check 3: names
    missing = names_missing(c["text"], haystack)
    if missing:
        return _drop(c, f"name_not_in_source: {', '.join(missing)}")

    # Check 4: the LLM judges, and must give a quote
    prompt = CRITIC_PROMPT.format(
        name=profile["name"], solution=profile["solution"], problem=profile["problem"],
        target_customer=profile["target_customer"], geography=profile["geography"],
        claim=c["text"], category=c["category"], source_text=haystack,
    )
    try:
        verdict = ask_structured(get_llm(), prompt, ClaimCheck)
    except Exception as e:
        return _drop(c, f"check_failed: {str(e)[:80]}")  # tried again in the next round

    if not verdict.supported:
        return _drop(c, f"not_supported_by_source: {verdict.reason}")

    # Check 5: the quote must really be in the source
    if not quote_in_source(verdict.evidence_quote, haystack):
        return _drop(c, "quote_not_found_in_source")

    # Check 6: relevance and category
    if verdict.best_category == "irrelevant":
        return _drop(c, f"not_relevant_to_idea: {verdict.reason}")
    if verdict.best_category != c["category"]:
        c["recategorized_from"] = c["category"]
        c["category"] = verdict.best_category

    c["evidence_quote"] = verdict.evidence_quote.strip()
    return c, None


# ---------------------------------------------------------------------------
# The differentiation-gap claim (analysis based on verified competitors)
# ---------------------------------------------------------------------------

def make_gap_claim(idea_text: str, profile: dict, verified: list):
    """Returns (claim, None), (None, dropped_claim) or (None, None)."""
    comps = [c for c in verified if c["category"] == "competitor"]
    if len(comps) < 2:
        return None, None

    facts = "\n".join(f"{i}. {c['text']}" for i, c in enumerate(comps, start=1))
    prompt = GAP_PROMPT.format(name=profile["name"], solution=profile["solution"], facts=facts)
    try:
        g = ask_structured(get_llm(), prompt, GapStatement)
    except Exception as e:
        print(f"  (gap analysis failed: {e})")
        return None, None
    if not g.has_gap:
        return None, None

    statement = clean_text(g.statement).strip()

    def fail(reason):
        return None, {"text": statement or "(empty)", "category": "differentiation_gap",
                      "source_ids": [], "reason": reason}

    based = sorted({n for n in g.based_on if 1 <= n <= len(comps)})
    if not statement or not g.feature.strip() or not based:
        return fail("gap_incomplete")
    if not statement.lower().startswith("among"):
        statement = "Among the competitors found, " + statement[0].lower() + statement[1:]

    # The feature must come from the founder's own idea
    words = [w for w in re.findall(r"[a-z]{4,}", norm(g.feature)) if w not in GENERIC_WORDS]
    if not words:
        return fail("gap_feature_unclear")
    idea_norm = norm(f"{idea_text} {profile['solution']} {profile['problem']}")
    if not any(w in idea_norm for w in words):
        return fail("feature_not_in_idea")

    # No verified competitor fact may already mention most of the feature
    for c in comps:
        ctext = norm(c["text"])
        if sum(w in ctext for w in words) / len(words) >= 0.6:
            return fail(f"feature_already_offered: {g.feature.strip()}")

    source_ids = sorted({i for n in based for i in comps[n - 1]["source_ids"]})
    return {
        "text": statement,
        "category": "differentiation_gap",
        "source_ids": source_ids,
        "derived": True,
        "evidence_quote": "",
        "based_on": [comps[n - 1]["text"] for n in based],
    }, None


# ---------------------------------------------------------------------------
# The graph node
# ---------------------------------------------------------------------------

def critic_node(state: ValidatorState) -> dict:
    run_id = state["run_id"]
    sources = state["sources"]

    # Start from earlier results. The gap claim is rebuilt every time, and
    # claims whose check crashed get a second chance.
    verified = [c for c in state["verified"] if c["category"] != "differentiation_gap"]
    dropped = [
        c for c in state["dropped"]
        if c["category"] != "differentiation_gap"
        and not str(c.get("reason", "")).startswith("check_failed")
    ]

    done = {norm(c["text"]) for c in verified + dropped}
    todo = [c for c in state["claims"] if norm(c["text"]) not in done]

    new_ok = 0
    for n, claim in enumerate(todo, start=1):
        print(f"  checking claim {n}/{len(todo)}")
        ok, bad = check_claim(claim, sources, state["past_notes"], state["profile"])
        if ok:
            verified.append(ok)
            new_ok += 1
        else:
            dropped.append(bad)

    gap_claim, gap_drop = make_gap_claim(state["idea_text"], state["profile"], verified)
    if gap_claim:
        verified.append(gap_claim)
    elif gap_drop:
        dropped.append(gap_drop)

    gaps = compute_gaps(verified)

    db.add_event(
        run_id, "critic",
        f"Checked {len(todo)} claim(s): {new_ok} verified, {len(todo) - new_ok} dropped",
    )
    if gaps:
        db.add_event(run_id, "critic", f"Missing verified evidence for: {', '.join(gaps)}")
    else:
        db.add_event(run_id, "critic", "Every research angle has verified evidence")

    db.save_claims(run_id, verified, dropped)
    return {"verified": verified, "dropped": dropped, "gaps": gaps}