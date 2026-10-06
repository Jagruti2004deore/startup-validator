import json

from app.state import initial_state
from app.agents.analyst import analyst_node

with open("tests/sample_run.json", encoding="utf-8") as f:
    saved = json.load(f)

state = initial_state("test-note", "study buddy app")
state["profile"] = saved["profile"]
state["past_notes"] = [
    "[note] Rejected a study-group matching app for students last year because "
    "every college class already has its own WhatsApp group."
]

result = analyst_node(state)
found = [c for c in result["claims"] if c["category"] == "conflict_with_past_notes"]

if not found:
    print("No conflict claim was created.")
for c in found:
    print("CLAIM:", c["text"])
    print("QUOTE:", c["note_quote"])
    print("quote is really in the note:", c["note_quote"] in state["past_notes"][0])