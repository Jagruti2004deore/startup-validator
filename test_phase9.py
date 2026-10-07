import json
import os
import re
import sys
import time

from app.db import init_db, create_run, get_events
from app.graph import graph
from app.agents.reporter import report_node
from app.state import initial_state

SAMPLE = "tests/sample_final.json"
REPORT_FILE = "tests/sample_report.md"
IDEA = (
    "A study-buddy app that matches college students in India into small groups "
    "for exam preparation, with a shared study planner and weekly mock quizzes."
)

os.makedirs("tests", exist_ok=True)
init_db()

# ---------- 1. get a finished run: load it, or run the whole agent ----------
state = None
if os.path.exists(SAMPLE) and "--fresh" not in sys.argv:
    try:
        with open(SAMPLE, encoding="utf-8") as f:
            state = json.load(f)
        needed = ("verified", "dropped", "sources", "score", "profile", "idea_text")
        if not all(k in state for k in needed):
            state = None
    except (json.JSONDecodeError, OSError):
        state = None
    if state is None:
        print("Saved file is empty or broken, running the full agent.")

if state is None:
    print("Running the full agent (5 to 8 minutes, rate-limit waits are normal)...")
    run_id = create_run(IDEA)
    start_state = initial_state(run_id, IDEA)
    final = dict(start_state)
    for step in graph.stream(start_state, config={"recursion_limit": 60}, stream_mode="updates"):
        for node, update in step.items():
            if update:
                final.update(update)
            print("-->", node)
    state = final
    with open(SAMPLE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print("saved", SAMPLE)
else:
    print("Loaded the saved run from", SAMPLE)

# ---------- 2. run only the Reporter, on a fresh run id ----------
state["run_id"] = create_run(state["idea_text"])
start = time.time()
report = report_node(state)["report"]
print(f"\nReporter finished in {time.time() - start:.0f}s\n")
print("=" * 70)
print(report)
print("=" * 70)

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)
print(f"\nsaved {REPORT_FILE}  (open it in VS Code and press Ctrl+Shift+V to see it formatted)")

# ---------- 3. checks ----------
body, _, sources_part = report.partition("## Sources")
cited = set(re.findall(r"\[(\d+)\]", body))
listed = set(re.findall(r"^\[(\d+)\]", sources_part, flags=re.M))
print("\n=== CHECKS ===")
print("citations with no source listed:", sorted(cited - listed) or "none (good)")
print("listed sources never cited:     ", sorted(listed - cited) or "none (good)")
print("verdict in report matches rules:", f"**Verdict: {state['score']['verdict']}**" in report)
print("raw [C#] tags left in report:   ", len(re.findall(r"\[C\d+\]", report)), "(expected 0)")

messages = [e["message"] for e in get_events(state["run_id"]) if e["node"] == "reporter"]
print("reporter event:", messages[-1] if messages else "missing")