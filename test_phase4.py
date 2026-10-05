from app.db import init_db, create_run, get_events
from app.state import initial_state
from app.agents.intake import intake_node, recall_node
from app.agents.researcher import plan_research, search_web

init_db()
idea = (
    "A study-buddy app that matches college students in India into small groups "
    "for exam preparation, with a shared study planner and weekly mock quizzes."
)
run_id = create_run(idea)
state = initial_state(run_id, idea)


def run(name, fn):
    print(f"\n=== {name} ===")
    state.update(fn(state))


run("1. INTAKE", intake_node)
for k, v in state["profile"].items():
    print(f"  {k}: {v}")

run("2. RECALL", recall_node)
print("  past notes:", state["past_notes"] or "none")

run("3. PLAN (round 1, all angles)", plan_research)
for q in state["queries"]:
    print("  -", q)

run("4. SEARCH (round 1)", search_web)
print("  sources:", len(state["sources"]))
for i, s in enumerate(state["sources"], start=1):
    print(f"  [{i}] {s['title'][:60]}  ({s['url'][:50]})")

# Simulate the Critic asking for a second round about two gaps
print("\n--- simulating a second round: gaps = pricing + market_size ---")
state["gaps"] = ["pricing", "market_size"]
state["loop_count"] = 1
before = len(state["sources"])

run("5. PLAN (round 2, gaps only)", plan_research)
for q in state["queries"]:
    print("  -", q)

run("6. SEARCH (round 2)", search_web)
print(f"  sources: {before} -> {len(state['sources'])}")

urls = [s["url"].split('#')[0].rstrip('/').lower() for s in state["sources"]]
print("\nduplicate URLs:", len(urls) - len(set(urls)))
print("\n=== EVENTS SAVED FOR THE UI ===")
for e in get_events(run_id):
    print(f"  {e['node']:<11} {e['message']}")