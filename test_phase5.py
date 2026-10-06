import json
import os
import sys
from collections import Counter

from app.db import init_db, create_run
from app.state import initial_state
from app.agents.intake import intake_node, recall_node
from app.agents.researcher import plan_research, search_web
from app.agents.analyst import analyst_node

SAMPLE = "tests/sample_run.json"
os.makedirs("tests", exist_ok=True)
init_db()

idea = (
    "A study-buddy app that matches college students in India into small groups "
    "for exam preparation, with a shared study planner and weekly mock quizzes."
)
state = initial_state(create_run(idea), idea)

# ---------- 1. Load saved data, or collect fresh data ----------
saved = None
if os.path.exists(SAMPLE) and "--fresh" not in sys.argv:
    try:
        with open(SAMPLE, encoding="utf-8") as f:
            saved = json.load(f)
        if not all(k in saved for k in ("profile", "sources", "past_notes")):
            saved = None
    except (json.JSONDecodeError, OSError):
        saved = None
    if saved is None:
        print("Saved file is empty or broken, collecting fresh data.")

if saved:
    state["profile"] = saved["profile"]
    state["sources"] = saved["sources"]
    state["past_notes"] = saved["past_notes"]
    print("Loaded saved sources:", len(state["sources"]))
else:
    for fn in (intake_node, recall_node, plan_research, search_web):
        state.update(fn(state))
    print("Collected sources:", len(state["sources"]))

# ---------- 2. Test the past-note path without touching real memory ----------
if not state["past_notes"]:
    state["past_notes"] = [
        "[note] Rejected a flashcard app for students last year because the market "
        "was crowded with Quizlet and Anki."
    ]
    print("(added a test past note)")

# ---------- 3. Run the Analyst ----------
state.update(analyst_node(state))
claims = state["claims"]
print(f"\nTotal claims: {len(claims)}")

print("\n=== BY CATEGORY ===")
for cat, n in Counter(c["category"] for c in claims).most_common():
    print(f"  {cat:<26} {n}")

# ---------- 4. Check the source numbers ----------
total = len(state["sources"])
bad_ids = [
    c for c in claims
    if not c["from_notes"] and any(not (1 <= i <= total) for i in c["source_ids"])
]
no_ids = [c for c in claims if not c["from_notes"] and not c["source_ids"]]
print(f"\nclaims citing a source number that does not exist: {len(bad_ids)}")
print(f"claims with no source at all: {len(no_ids)}")

# ---------- 5. Show sample claims ----------
print("\n=== SAMPLE CLAIMS ===")
shown = Counter()
for c in claims:
    if shown[c["category"]] >= 2:
        continue
    shown[c["category"]] += 1
    print(f"\n[{c['category']}] {c['text']}")
    if c["from_notes"]:
        print(f"   from your note: \"{c.get('note_quote', '')}\"")
    for i in c["source_ids"]:
        if 1 <= i <= total:
            print(f"   -> [{i}] {state['sources'][i - 1]['title'][:60]}")

# ---------- 6. A second call must not duplicate claims ----------
before = len(state["claims"])
state.update(analyst_node(state))
print(f"\nsecond call adds {len(state['claims']) - before} new claims (should be 0)")

# ---------- 7. Save everything for Phase 6 ----------
with open(SAMPLE, "w", encoding="utf-8") as f:
    json.dump(
        {
            "profile": state["profile"],
            "sources": state["sources"],
            "past_notes": state["past_notes"],
            "claims": state["claims"],
        },
        f, indent=2, ensure_ascii=False,
    )
print("saved", SAMPLE)