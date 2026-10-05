from app import db
from app.config import MIN_MEMORY_SCORE
from app.llm_utils import ask_structured, get_llm
from app.memory import search_memory
from app.models import IdeaProfile
from app.prompts import INTAKE_PROMPT
from app.state import ValidatorState


def intake_node(state: ValidatorState) -> dict:
    """Turn the raw idea text into a structured profile."""
    idea = state["idea_text"].strip()
    if len(idea) < 10:
        raise ValueError("Please describe the idea in at least one full sentence.")

    profile = ask_structured(get_llm(), INTAKE_PROMPT.format(idea_text=idea), IdeaProfile)
    db.add_event(
        state["run_id"], "intake",
        f"Understood the idea: {profile.name} ({profile.category}, {profile.geography})",
    )
    return {"profile": profile.model_dump()}


def recall_node(state: ValidatorState) -> dict:
    """Ask Pinecone for the founder's similar past notes and reports."""
    p = state["profile"]
    query = f"{p['name']}. {p['problem']} {p['solution']} Target: {p['target_customer']}."

    try:
        hits = search_memory(query, top_k=3, min_score=MIN_MEMORY_SCORE)
    except Exception as e:
        # memory is a bonus; the run must continue without it
        db.add_event(state["run_id"], "recall", "Memory unavailable, continuing without it")
        print(f"  (memory search failed: {e})")
        return {"past_notes": []}

    notes = [f"[{h['type']}] {h['text']}" for h in hits]
    message = (
        f"Found {len(notes)} similar past note(s)" if notes
        else "No similar past notes found"
    )
    db.add_event(state["run_id"], "recall", message)
    return {"past_notes": notes}