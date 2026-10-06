from app import db
from app.config import ANALYST_BATCH_SIZE, MAX_CLAIMS_PER_BATCH
from app.llm_utils import ask_structured, get_llm
from app.models import ClaimList, NoteConflict
from app.prompts import ANALYST_PROMPT, NOTE_CONFLICT_PROMPT
from app.state import ValidatorState
from app.utils import today_note, clean_text

# Only these kinds of claims come straight from sources
ALLOWED = {
    "competitor", "pricing", "market_size",
    "demand_signal", "recent_activity", "failure_or_risk",
}


def _format_batch(sources: list, start: int, end: int) -> str:
    """Numbered sources. The number is the global position + 1."""
    blocks = []
    for i in range(start, end):
        s = sources[i]
        blocks.append(f"[{i + 1}] {s['title']} - {s['url']}\n{s['content']}")
    return "\n\n".join(blocks)


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def analyst_node(state: ValidatorState) -> dict:
    sources = state["sources"]
    claims = list(state["claims"])
    seen = {_norm(c["text"]) for c in claims}
    p = state["profile"]
    run_id = state["run_id"]

    # 1. Read only the sources we have not read yet
    for start in range(state["analyzed_count"], len(sources), ANALYST_BATCH_SIZE):
        end = min(start + ANALYST_BATCH_SIZE, len(sources))
        prompt = today_note() + ANALYST_PROMPT.format(
            name=p["name"], solution=p["solution"],
            target_customer=p["target_customer"], geography=p["geography"],
            sources=_format_batch(sources, start, end),
            max_claims=MAX_CLAIMS_PER_BATCH,
        )
        try:
            result = ask_structured(get_llm(), prompt, ClaimList)
        except Exception as e:
            # one failed batch must not kill the run
            print(f"  (analyst batch {start + 1}-{end} failed: {e})")
            db.add_event(run_id, "analyst", f"Could not read sources {start + 1}-{end}")
            continue

        found = 0
        for c in result.claims:
            text = clean_text(c.text).strip()
            if c.category not in ALLOWED or not text or _norm(text) in seen:
                continue
            seen.add(_norm(text))
            claims.append({
                "text": text,
                "category": c.category,
                "source_ids": list(c.source_ids),
                "from_notes": False,
            })
            found += 1
        db.add_event(run_id, "analyst", f"Read sources {start + 1}-{end}: {found} claim(s)")

    # 2. Compare the idea with past notes (first round only)
    if state["loop_count"] == 0 and state["past_notes"]:
        notes_text = "\n".join(f"- {n}" for n in state["past_notes"])
        prompt = NOTE_CONFLICT_PROMPT.format(
            name=p["name"], problem=p["problem"], solution=p["solution"], notes=notes_text,
        )
        try:
            link = ask_structured(get_llm(), prompt, NoteConflict)
            if link.relevant and link.claim_text.strip() and link.note_quote.strip():
                claims.append({
                    "text": clean_text(link.claim_text).strip(),
                    "category": "conflict_with_past_notes",
                    "source_ids": [],
                    "from_notes": True,
                    "note_quote": link.note_quote.strip(),
                })
                db.add_event(run_id, "analyst", "Linked the idea to a past note")
        except Exception as e:
            print(f"  (past-note check failed: {e})")

    return {"claims": claims, "analyzed_count": len(sources)}