import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import db  # noqa: E402

# evaluation runs use their own database, so your real runs stay clean
db.DB_PATH = str(ROOT / "eval_runs.db")
db.init_db()

import app.agents.intake as intake_mod  # noqa: E402

# and an EMPTY memory, so your personal notes cannot influence the verdicts
_real_search = intake_mod.search_memory


def _empty_memory_search(query, top_k=3, min_score=0.0):
    return _real_search(query, top_k=top_k, min_score=min_score, namespace="eval-empty")


intake_mod.search_memory = _empty_memory_search

from app.config import MODEL_NAME  # noqa: E402
from app.graph import run_validator  # noqa: E402
from app.llm_utils import DailyLimitError  # noqa: E402
from tests.eval.common import (  # noqa: E402
    KEY_BY_VERDICT, RESULTS_DIR, load_ideas, ratio, summarize_verdicts,
)


def results_path(model: str) -> Path:
    return RESULTS_DIR / f"verdicts_{model.replace('/', '_')}.json"


def load_saved(model: str) -> dict:
    path = results_path(model)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"model": model, "runs": {}}


def save(saved: dict) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    results_path(saved["model"]).write_text(json.dumps(saved, indent=2), encoding="utf-8")


def run_one(idea: dict) -> dict:
    run_id = db.create_run(idea["idea"])
    start = time.time()
    final = run_validator(run_id, idea["idea"])
    events = db.get_events(run_id)
    template = any("template" in e["message"] for e in events if e["node"] == "reporter")
    score = final["score"]
    return {
        "id": idea["id"], "group": idea["group"], "status": "done",
        "verdict": score["verdict"], "verdict_key": KEY_BY_VERDICT.get(score["verdict"], "?"),
        "evidence_score": score["evidence_score"], "max_score": score["max_score"],
        "competitors": score["competitors_found"], "crowdedness": score["crowdedness"],
        "verified": len(final["verified"]), "dropped": len(final["dropped"]),
        "sources": len(final["sources"]), "loops": final["loop_count"],
        "seconds": round(time.time() - start),
        "summary": "template" if template else "llm",
    }


def print_report(saved: dict, ideas: list) -> None:
    by_id = {i["id"]: i for i in ideas}
    rows = []
    print(f"\nVERDICT EVALUATION (model: {saved['model']})")
    print(f"{'id':<4} {'group':<8} {'verdict':<10} {'score':<6} {'comps':<6} {'verified':<9} "
          f"{'loops':<6} {'in range'}")
    for idea_id, r in saved["runs"].items():
        if r.get("status") != "done" or idea_id not in by_id:
            continue
        idea = by_id[idea_id]
        row = {"id": idea_id, "verdict_key": r["verdict_key"],
               "acceptable": idea["acceptable"], "must_not": idea["must_not"]}
        rows.append(row)
        flag = "yes" if r["verdict_key"] in idea["acceptable"] else (
            "NO (overconfident)" if r["verdict_key"] in idea["must_not"] else "no")
        print(f"{idea_id:<4} {idea['group']:<8} {r['verdict_key']:<10} "
              f"{r['evidence_score']}/{r['max_score']:<4} {r['competitors']:<6} "
              f"{r['verified']:<9} {r['loops']:<6} {flag}")
    if not rows:
        print("(no finished runs yet)")
        return
    s = summarize_verdicts(rows)
    llm_summaries = sum(1 for r in saved["runs"].values()
                        if r.get("status") == "done" and r.get("summary") == "llm")
    print("\n" + "=" * 60)
    print(f"Ideas finished:              {s['total']} of {len(ideas)}")
    print(f"Verdict within range:        {ratio(len(s['within_range']), s['total'])}")
    print(f"Overconfident verdicts:      {s['overconfident'] or 'none'}")
    print(f"Ended as Unclear:            {s['unclear'] or 'none'}")
    print(f"AI summary passed checks:    {ratio(llm_summaries, s['total'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate verdicts on test ideas (resumable).")
    parser.add_argument("--limit", type=int, default=2, help="max NEW ideas to run now")
    parser.add_argument("--only", default="", help="comma-separated idea ids, e.g. v01,v04")
    parser.add_argument("--force", action="store_true", help="rerun ideas that are already done")
    parser.add_argument("--report", action="store_true", help="only print saved results")
    args = parser.parse_args()

    ideas = load_ideas()
    chosen = ideas
    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        chosen = [i for i in ideas if i["id"] in wanted]

    saved = load_saved(MODEL_NAME)

    if not args.report:
        todo = [i for i in chosen
                if args.force or saved["runs"].get(i["id"], {}).get("status") != "done"]
        todo = todo[: args.limit]
        if not todo:
            print("Nothing left to run for this model.")
        for n, idea in enumerate(todo, start=1):
            print(f"\n[{n}/{len(todo)}] {idea['id']} ({idea['group']}): {idea['idea'][:70]}")
            try:
                saved["runs"][idea["id"]] = run_one(idea)
                r = saved["runs"][idea["id"]]
                print(f"   -> {r['verdict']} | evidence {r['evidence_score']}/{r['max_score']} "
                      f"| {r['seconds']}s")
            except DailyLimitError:
                print("   The daily token limit was reached. Run the same command again later.")
                break
            except Exception as e:
                saved["runs"][idea["id"]] = {"id": idea["id"], "status": "error", "error": str(e)[:150]}
                print(f"   failed: {str(e)[:150]}")
            save(saved)

    print_report(saved, ideas)


if __name__ == "__main__":
    main()