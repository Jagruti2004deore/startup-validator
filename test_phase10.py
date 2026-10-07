import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
KEY = os.getenv("APP_API_KEY", "")
HEADERS = {"X-API-Key": KEY} if KEY else {}

CHECK_ONLY = "--check" in sys.argv
ASSUME_YES = "--yes" in sys.argv
words = [a for a in sys.argv[1:] if not a.startswith("--")]
IDEA = " ".join(words) or (
    "A study-buddy app that matches college students in India into small groups "
    "for exam preparation, with a shared study planner and weekly mock quizzes."
)


def get(path, **kwargs):
    return requests.get(f"{BASE}{path}", headers=HEADERS, timeout=30, **kwargs)


# ---------- is the server running? ----------
try:
    health = requests.get(f"{BASE}/health", timeout=10).json()
except requests.exceptions.ConnectionError:
    sys.exit(
        f"The server is not running at {BASE}.\n"
        "Open a second terminal, activate (venv), and run:\n"
        "    uvicorn app.api:app --port 8000\n"
        "Wait for 'Application startup complete', then run this script again."
    )
print("health:", health)

# ---------- cheap checks, no tokens ----------
if CHECK_ONLY:
    runs = get("/runs")
    print("GET /runs:", runs.status_code, f"{len(runs.json())} run(s)" if runs.ok else runs.text)
    notes = get("/notes")
    print("GET /notes:", notes.status_code, f"{len(notes.json())} note(s)" if notes.ok else notes.text)
    print("\nAll checks done. No tokens were used.")
    sys.exit(0)

# ---------- a real run ----------
if not ASSUME_YES:
    answer = input("This starts a REAL run and uses most of a day's free Groq tokens. Continue? (yes/no) ")
    if answer.strip().lower() != "yes":
        sys.exit("Cancelled.")

response = requests.post(f"{BASE}/validate", json={"idea": IDEA}, headers=HEADERS, timeout=30)
print("start:", response.status_code, response.json())
if response.status_code != 202:
    sys.exit("The run did not start.")

run_id = response.json()["run_id"]
after = 0
while True:
    data = get(f"/runs/{run_id}", params={"after": after}).json()
    for event in data["events"]:
        print(f"  [{event['time'][11:19]}] {event['node']:<11} {event['message']}")
        after = event["id"]
    if data["status"] != "running":
        break
    time.sleep(3)

print(f"\nstatus: {data['status']}  verdict: {data['verdict']}  evidence score: {data['evidence_score']}")
if data["status"] == "done":
    report = get(f"/runs/{run_id}/report").json()
    print(f"verified claims: {len(report['verified'])}  removed claims: {len(report['dropped'])}  "
          f"sources: {len(report['sources'])}")
    print("\n--- first 25 lines of the report ---")
    print("\n".join(report["report_md"].splitlines()[:25]))