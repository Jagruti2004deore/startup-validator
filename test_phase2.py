from pydantic import ValidationError
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, MODEL_NAME
from app.db import (
    init_db, create_run, update_run, get_run, add_event, get_events,
    save_sources, get_sources, save_claims, get_claims, add_note, list_notes,
)
from app.models import Claim, IdeaProfile
from app.llm_utils import ask_structured

# ---------- Part A: the database ----------
print("=== A. DATABASE ===")
init_db()
run_id = create_run("A study-buddy app for college students in India")
print("created run:", run_id)

add_event(run_id, "intake", "Parsed the idea")
add_event(run_id, "researcher", "Found 2 sources")
print("events:", [e["node"] for e in get_events(run_id)])

save_sources(run_id, [
    {"url": "https://example.com/a", "title": "Source A", "content": "Competitor X charges $10 a month."},
    {"url": "https://example.com/b", "title": "Source B", "content": "The market grew 12% in 2025."},
])
print("sources saved:", len(get_sources(run_id)))

verified = [{"text": "Competitor X charges $10 a month.", "category": "pricing", "source_ids": [1]}]
dropped = [{"text": "The market is worth $5 billion.", "category": "market_size",
            "source_ids": [2], "reason": "number not found in source"}]
save_claims(run_id, verified, dropped)
for c in get_claims(run_id):
    print(f"  claim [{c['status']}] {c['text']} -> sources {c['source_nos']} {c['drop_reason'] or ''}")

update_run(run_id, status="done", verdict="Proceed with caution", evidence_score=5)
print("run now:", {k: get_run(run_id)[k] for k in ("status", "verdict", "evidence_score")})

add_note("Rejected a flashcard app last year because of crowded market.")
print("notes saved:", len(list_notes()))

# ---------- Part B: the forms reject bad data ----------
print("\n=== B. FORMS ===")
try:
    Claim(text="Something", category="made_up_category", source_ids=[1])
    print("ERROR: bad category was accepted")
except ValidationError:
    print("bad category rejected (good)")

# ---------- Part C: the LLM fills the idea form ----------
print("\n=== C. LLM FILLS THE IDEA FORM ===")
llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY, max_retries=0)
profile = ask_structured(
    llm,
    "Turn this startup idea into the form.\nIdea: A study-buddy app that matches "
    "college students in India for group exam preparation.",
    IdeaProfile,
)
print(profile.model_dump_json(indent=2))