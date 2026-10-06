import json
import time
from collections import Counter

from app.db import init_db, create_run
from app.state import initial_state
import app.agents.critic as critic_mod
from app.agents.critic import critic_node, norm

with open("tests/sample_run.json", encoding="utf-8") as f:
    saved = json.load(f)

init_db()
idea = "A study-buddy app that matches college students in India into small groups for exam preparation."
state = initial_state(create_run(idea), idea)
state["profile"] = saved["profile"]
state["sources"] = saved["sources"]
state["past_notes"] = saved["past_notes"]
state["claims"] = list(saved["claims"])

# Three lies. The Critic must drop all of them.
fakes = [
    {"text": "Kahoot+ Study charges $49 per month.", "category": "pricing",
     "source_ids": [2], "from_notes": False},
    {"text": "Duolingo offers group study rooms for college students.", "category": "competitor",
     "source_ids": [1], "from_notes": False},
    {"text": "Quizlet has 500 million users.", "category": "demand_signal",
     "source_ids": [99], "from_notes": False},
]
state["claims"].extend(fakes)

# count the LLM calls the Critic makes
calls = {"n": 0}
real = critic_mod.ask_structured


def counting(*args, **kwargs):
    calls["n"] += 1
    return real(*args, **kwargs)


critic_mod.ask_structured = counting

print(f"Claims to check: {len(state['claims'])} (including {len(fakes)} fakes)\n")
start = time.time()
state.update(critic_node(state))
print(f"\nfirst run: {calls['n']} LLM calls, {time.time() - start:.0f}s")

verified, dropped = state["verified"], state["dropped"]
print(f"\nVERIFIED: {len(verified)}   DROPPED: {len(dropped)}")

print("\n=== DROP REASONS ===")
reasons = Counter(str(d["reason"]).split(":")[0] for d in dropped)
for r, n in reasons.most_common():
    print(f"  {r:<32} {n}")

print("\n=== DROPPED CLAIMS ===")
for d in dropped:
    print(f"\n[{d['category']}] {d['text'][:110]}")
    print(f"   reason: {d['reason'][:130]}")

print("\n=== VERIFIED CLAIMS ===")
for v in verified:
    tag = f" (was {v['recategorized_from']})" if v.get("recategorized_from") else ""
    print(f"\n[{v['category']}]{tag} {v['text'][:110]}")
    if v.get("derived"):
        print("   ANALYSIS based on verified competitors")
    elif v.get("evidence_quote"):
        print(f"   quote: \"{v['evidence_quote'][:110]}\"")

print("\nGAPS (angles still missing verified evidence):", state["gaps"] or "none")

dropped_texts = {norm(d["text"]) for d in dropped}
caught = sum(norm(f["text"]) in dropped_texts for f in fakes)
print(f"\nFAKE CLAIMS CAUGHT: {caught}/{len(fakes)}")

calls["n"] = 0
state.update(critic_node(state))
print(f"second run: {calls['n']} LLM calls (expected 0 or 1: only the gap analysis repeats)")