import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import app.agents.critic as critic_mod  # noqa: E402
from app.agents.critic import check_claim  # noqa: E402
from app.config import MODEL_NAME  # noqa: E402
from app.llm_utils import DailyLimitError  # noqa: E402
from tests.eval.common import (  # noqa: E402
    PROFILE, RESULTS_DIR, build_inputs, load_cases, ratio, summarize_critic,
)


def reason_code(reason) -> str:
    return str(reason or "").split(":")[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the critic on hand-written cases.")
    parser.add_argument("--rules-only", action="store_true", help="skip the LLM (free)")
    parser.add_argument("--only", default="", help="comma-separated case ids, e.g. c14,c17")
    args = parser.parse_args()

    cases = load_cases()
    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        cases = [c for c in cases if c["id"] in wanted]

    if args.rules_only:
        def refuse(*a, **k):
            raise RuntimeError("rules-only run")
        critic_mod.ask_structured = refuse

    mode = "rules only" if args.rules_only else f"full ({MODEL_NAME})"
    print(f"CRITIC EVALUATION: {len(cases)} cases, mode: {mode}\n")

    rows = []
    start = time.time()
    for case in cases:
        claim, sources, notes = build_inputs(case)
        try:
            ok, bad = check_claim(claim, sources, notes, PROFILE)
        except DailyLimitError:
            print("\nThe daily token limit was reached. Run again later "
                  "(use --only to run just the cases that are missing).")
            break

        code = reason_code(bad["reason"]) if bad else ""
        if code == "check_failed":
            got = "skipped (needs LLM)" if args.rules_only else "error"
        else:
            got = "verified" if ok else "dropped"

        if got == case["expected"]:
            note = "OK"
            if got == "dropped" and code not in case["expected_reasons"]:
                note = f"OK (different reason: {code})"
        elif got in ("verified", "dropped"):
            note = "MISS"
        else:
            note = "-"
        print(f"{case['id']}  {case['kind'][:44]:<44} expected {case['expected']:<9} "
              f"got {got:<20} {note}")
        rows.append({
            "id": case["id"], "kind": case["kind"], "layer": case["layer"],
            "expected": case["expected"], "got": got, "reason": code,
            "expected_reasons": case["expected_reasons"],
        })

    s = summarize_critic(rows)
    print("\n" + "=" * 60)
    print(f"Cases scored:                {s['scored']} of {len(rows)} run")
    print(f"Overall accuracy:            {ratio(s['correct'], s['scored'])}")
    print(f"Bad claims caught:           {ratio(*s['bad_caught'])}")
    print(f"Good claims kept:            {ratio(*s['good_kept'])}")
    print(f"Unsafe passes (bad accepted): {s['unsafe_passes'] or 'none'}")
    print(f"False drops (good removed):   {s['false_drops'] or 'none'}")
    print(f"Code rules:                  {ratio(*s['by_layer']['code'])}")
    print(f"LLM judgement:               {ratio(*s['by_layer']['llm'])}")
    print(f"Time: {time.time() - start:.0f}s")

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_model = MODEL_NAME.replace("/", "_")
    path = RESULTS_DIR / f"critic_{safe_model}_{'rules' if args.rules_only else 'full'}_{stamp}.json"
    path.write_text(json.dumps({"model": MODEL_NAME, "mode": mode, "summary": s, "cases": rows},
                               indent=2, default=list), encoding="utf-8")
    print(f"\nsaved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()