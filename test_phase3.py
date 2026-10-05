import time

from app.db import init_db
from app.memory import (
    add_note, save_report_summary, search_memory, clear_namespace,
)

TEST_NS = "test"
init_db()
clear_namespace(TEST_NS)  # start clean

print("=== 1. STORE NOTES ===")
notes = [
    "Rejected a flashcard app for students last year because the market was crowded with Quizlet and Anki.",
    "Prefers B2B SaaS ideas with monthly subscriptions over consumer apps.",
    "Tried selling cold-chain software to rural dairy farms, but farmers had no budget for it.",
    "Interested in tools that help Indian college students prepare for campus placements.",
]
for n in notes:
    chunks = add_note(n, namespace=TEST_NS, save_to_db=False)
    print(f"stored ({chunks} chunk): {n[:60]}...")

long_note = "Market research diary. " + ("The edtech space in India is competitive and price sensitive. " * 40)
print("long note chunks:", add_note(long_note, namespace=TEST_NS, save_to_db=False))


def search_when_ready(query, tries=15):
    """New vectors can take a few seconds to become searchable, so we retry."""
    for _ in range(tries):
        hits = search_memory(query, top_k=3, namespace=TEST_NS)
        if hits:
            return hits
        time.sleep(2)
    return []


print("\n=== 2. RECALL ===")
for q in ["a study app for students preparing for exams",
          "software for farmers and agriculture"]:
    print(f"\nQuery: {q}")
    for h in search_when_ready(q):
        print(f"  {h['score']}  [{h['type']}]  {h['text'][:70]}")

print("\n=== 3. PAST REPORT ===")
save_report_summary("test0001", "An app for placement preparation", "Proceed with caution",
                    "Crowded market but a clear gap in company-specific prep.",
                    namespace=TEST_NS)
for h in search_when_ready("placement preparation tool for engineering students"):
    print(f"  {h['score']}  [{h['type']}]  {h['text'][:70]}")

clear_namespace(TEST_NS)
print("\nCleaned up the test data.")