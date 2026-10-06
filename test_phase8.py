import sys
import time
from collections import Counter

from app.db import init_db, create_run, get_run, get_events
from app.graph import graph
from app.scoring import format_score
from app.state import initial_state

DEFAULT_IDEA = (
    "A study-buddy app that matches college students in India into small groups "
    "for exam preparation, with a shared study planner and weekly mock quizzes."
)
idea = " ".join(sys.argv[1:]) or DEFAULT_IDEA

init_db()
run_id = create_run(idea)
state = initial_state(run_id, idea)
final = dict(state)
all_queries = []

print(f"Idea: {idea}\nRun id: {run_id}\n")
start = time.time()

for step in graph.stream(state, config={"recursion_limit": 60}, stream_mode="updates"):
    for node, update in step.items():
        if not update:        # a node that changes nothing reports None
            print(f"--> {node}")
            continue
        final.update(update)
        print(f"--> {node}")
        if node == "intake":
            p = update["profile"]
            print(f"     {p['name']} | {p['category']} | {p['geography']}")
        elif node == "recall":
            print(f"     similar past notes: {len(update['past_notes'])}")
        elif node == "plan_research":
            for q in update["queries"]:
                print("     query:", q)
                all_queries.append(q)
        elif node == "search_web":
            print(f"     sources so far: {len(update['sources'])}")
        elif node == "analyst":
            print(f"     claims so far: {len(update['claims'])}")
        elif node == "critic":
            print(f"     verified: {len(update['verified'])}  dropped: {len(update['dropped'])}")
            print(f"     gaps: {update['gaps'] or 'none'}")
        elif node == "prepare_retry":
            print(f"     starting round {update['loop_count']}")
        elif node == "score":
            print(f"     verdict: {update['verdict']}")

print(f"\nFinished in {time.time() - start:.0f}s")
print("\n=== FINAL ===")
print(f"loop rounds used: {final['loop_count']}   sources: {len(final['sources'])}   "
      f"claims: {len(final['claims'])}")
print(f"verified: {len(final['verified'])}   dropped: {len(final['dropped'])}")

keys = [" ".join(q.lower().split()) for q in all_queries]
repeats = len(keys) - len(set(keys))
print(f"queries planned: {len(all_queries)}   repeated queries: {repeats}  (expected 0)")

print("\nverified by category:")
for cat, n in Counter(c["category"] for c in final["verified"]).most_common():
    print(f"  {cat:<26} {n}")

print("\ndrop reasons:")
for reason, n in Counter(str(d["reason"]).split(":")[0] for d in final["dropped"]).most_common():
    print(f"  {reason:<32} {n}")

print("\n=== VERIFIED CLAIMS (read these and judge the verdict yourself) ===")
for c in final["verified"]:
    print(f"  [{c['category']}] {c['text'][:100]}")

print("\n=== SCORE ===")
print(format_score(final["score"]))

run = get_run(run_id)
print(f"\ndatabase: status={run['status']}, verdict={run['verdict']}, "
      f"evidence_score={run['evidence_score']}, events={len(get_events(run_id))}")