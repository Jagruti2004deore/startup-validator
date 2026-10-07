import os
import time

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

try:
    from ui.helpers import (
        TOTAL_ITEMS, NODE_ICONS, claim_rows, dropped_rows, short, source_lines, verdict_kind,
    )
except ModuleNotFoundError:  # when started with: streamlit run ui/streamlit_app.py
    from helpers import (
        TOTAL_ITEMS, NODE_ICONS, claim_rows, dropped_rows, short, source_lines, verdict_kind,
    )

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("APP_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

st.set_page_config(page_title="Startup Idea Validator", page_icon="🧭", layout="wide")


# ---------------------------------------------------------------------------
# Talking to the server
# ---------------------------------------------------------------------------

def api(method: str, path: str, **kwargs):
    """Returns (ok, data, error_message)."""
    try:
        response = requests.request(
            method, f"{API_URL}{path}", headers=HEADERS, timeout=30, **kwargs
        )
    except requests.exceptions.ConnectionError:
        return False, None, (
            f"Cannot reach the server at {API_URL}. "
            "Start it in another terminal with: uvicorn app.api:app --port 8000"
        )
    except requests.exceptions.RequestException as e:
        return False, None, f"The request failed: {e}"

    if response.ok:
        return True, response.json(), ""
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    if isinstance(detail, list):  # input validation errors
        detail = "; ".join(str(d.get("msg", d)) for d in detail)
    return False, None, str(detail)


# ---------------------------------------------------------------------------
# Live view and results
# ---------------------------------------------------------------------------

def watch_run(run_id: str) -> None:
    """Show the agents' steps live until the run finishes."""
    after = 0
    with st.status("The agents are working. This can take several minutes...", expanded=True) as box:
        while True:
            ok, data, err = api("GET", f"/runs/{run_id}", params={"after": after})
            if not ok:
                box.update(label="Lost contact with the server", state="error")
                st.error(err)
                return
            for event in data["events"]:
                icon = NODE_ICONS.get(event["node"], "•")
                box.write(f"{icon} **{event['node']}**: {event['message']}")
                after = event["id"]
            if data["status"] != "running":
                break
            time.sleep(2)
        if data["status"] == "done":
            box.update(label="Finished", state="complete", expanded=False)
        else:
            box.update(label="The run failed", state="error", expanded=True)


def show_result(run_id: str, status: dict) -> None:
    if status["status"] == "running":
        st.info("This run is still going. Open this page again in a minute.")
        return

    if status["status"] == "failed":
        st.error("This run failed.")
        if status["events"]:
            st.write(f"Last message: {status['events'][-1]['message']}")
        with st.expander("Event log"):
            st.code("\n".join(f"{e['time'][11:19]}  {e['node']:<11} {e['message']}"
                              for e in status["events"]), language=None)
        return

    ok, report, err = api("GET", f"/runs/{run_id}/report")
    if not ok:
        st.error(err)
        return
    if not report["report_md"]:
        st.info("This run has no report.")
        return

    banner = f"Verdict: {report['verdict']}   |   Evidence score: {report['evidence_score']} of {TOTAL_ITEMS}"
    getattr(st, verdict_kind(report["verdict"]))(banner)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Evidence score", f"{report['evidence_score']} of {TOTAL_ITEMS}")
    c2.metric("Verified claims", len(report["verified"]))
    c3.metric("Removed claims", len(report["dropped"]))
    c4.metric("Sources collected", len(report["sources"]))

    tab_report, tab_evidence, tab_removed, tab_sources, tab_log = st.tabs(
        ["Report", "Evidence", "Removed claims", "Sources", "Log"]
    )

    with tab_report:
        st.markdown(report["report_md"])
        st.download_button(
            "Download report (.md)", report["report_md"],
            file_name=f"validation_{run_id}.md", mime="text/markdown",
        )

    with tab_evidence:
        st.caption("Every claim here passed the critic's checks against its source text.")
        rows = claim_rows(report["verified"], report["sources"])
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True)
        else:
            st.info("No claims were verified.")

    with tab_removed:
        st.caption("These claims were dropped because they failed a check. "
                   "This is the critic at work.")
        rows = dropped_rows(report["dropped"])
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True)
        else:
            st.info("No claims were removed.")

    with tab_sources:
        st.caption("Collection order. These numbers differ from the numbers inside the report.")
        st.markdown("\n".join(source_lines(report["sources"])) or "No sources.")

    with tab_log:
        st.code("\n".join(f"{e['time'][11:19]}  {e['node']:<11} {e['message']}"
                          for e in status["events"]), language=None)


def follow(run_id: str) -> None:
    ok, status, err = api("GET", f"/runs/{run_id}")
    if not ok:
        st.error(err)
        return
    if status["status"] == "running":
        watch_run(run_id)
        ok, status, err = api("GET", f"/runs/{run_id}")
        if not ok:
            st.error(err)
            return
    st.caption(f"Run {run_id}")
    show_result(run_id, status)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def validate_page() -> None:
    st.title("🧭 Startup Idea Validator")
    st.caption(
        "Researcher, analyst and critic agents look for competitors, check every claim "
        "against its source, and score the idea by fixed rules. "
        "If the evidence is weak, the report says so."
    )
    idea = st.text_area(
        "Describe your startup idea", height=130, max_chars=1500,
        placeholder="e.g. An app that matches college students in India into small groups "
                    "for exam preparation, with a shared planner and weekly mock quizzes.",
    )
    if st.button("Validate", type="primary"):
        ok, data, err = api("POST", "/validate", json={"idea": idea})
        if ok:
            st.session_state["run_id"] = data["run_id"]
        else:
            st.error(err)

    run_id = st.session_state.get("run_id")
    if run_id:
        follow(run_id)


def history_page() -> None:
    st.title("Past runs")
    ok, runs, err = api("GET", "/runs", params={"limit": 50})
    if not ok:
        st.error(err)
        return
    if not runs:
        st.info("No runs yet.")
        return

    rows = [{
        "Run": r["id"],
        "Idea": short(r["idea_text"], 80),
        "Status": r["status"],
        "Verdict": r["verdict"] or "-",
        "Score": "-" if r["evidence_score"] is None else r["evidence_score"],
        "Started": (r["created_at"] or "").replace("T", " "),
    } for r in runs]
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    labels = {r["id"]: f"{r['id']}  |  {short(r['idea_text'], 60)}  |  {r['status']}" for r in runs}
    choice = st.selectbox("Open a run", options=list(labels), format_func=lambda rid: labels[rid])
    if st.button("Open"):
        st.session_state["history_run"] = choice

    run_id = st.session_state.get("history_run")
    if run_id:
        ok, status, err = api("GET", f"/runs/{run_id}")
        if ok:
            st.divider()
            st.caption(f"Run {run_id}: {short(status['idea'], 120)}")
            show_result(run_id, status)
        else:
            st.error(err)


def notes_page() -> None:
    st.title("My notes")
    st.caption(
        "The agent searches these notes when it validates a new idea, for example to warn you "
        "that you rejected something similar before. Write only what you want it to remember."
    )
    text = st.text_area("New note", height=100, max_chars=4000,
                        placeholder="e.g. I rejected a flashcard app because the market is crowded.")
    if st.button("Save note", type="primary"):
        ok, data, err = api("POST", "/notes", json={"text": text})
        if ok:
            st.success("Saved to memory.")
        else:
            st.error(err)

    ok, notes, err = api("GET", "/notes")
    if not ok:
        st.error(err)
        return
    st.subheader(f"Saved notes ({len(notes)})")
    for note in notes:
        st.markdown(f"- {note['text']}  \n  *{(note['created_at'] or '')[:10]}*")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

page = st.sidebar.radio("Go to", ["Validate an idea", "Past runs", "My notes"])

ok, health, err = api("GET", "/health")
if ok:
    st.sidebar.caption(f"Server online | Model: {health['model']}")
    if "20b" in health["model"]:
        st.sidebar.warning("The smaller model is in use. Results can be weaker.")
else:
    st.sidebar.error(err)

if page == "Validate an idea":
    validate_page()
elif page == "Past runs":
    history_page()
else:
    notes_page()