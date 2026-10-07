from langgraph.graph import StateGraph, START, END

from app import db
from app.agents.analyst import analyst_node
from app.agents.critic import critic_node
from app.agents.intake import intake_node, recall_node
from app.agents.reporter import report_node
from app.agents.researcher import plan_research, search_web
from app.config import MAX_LOOPS, MAX_SOURCES_TOTAL, GAP_ROUND_MAX_QUERIES
from app.scoring import score_node
from app.state import ValidatorState, initial_state


def safe(name: str, fn):
    """If a step crashes, record it in the run's events and mark the run as failed."""
    def wrapper(state):
        try:
            return fn(state)
        except Exception as e:
            db.add_event(state["run_id"], name, f"Stopped with an error: {str(e)[:150]}")
            db.update_run(state["run_id"], status="failed")
            raise
    return wrapper


def prepare_retry(state: ValidatorState) -> dict:
    """Start another research round. This is the step that turns the loop on."""
    round_no = state["loop_count"] + 1
    angles = ", ".join(state["gaps"][:GAP_ROUND_MAX_QUERIES])
    db.add_event(state["run_id"], "loop", f"Round {round_no}: searching again for {angles}")
    return {"loop_count": round_no}


def finish_node(state: ValidatorState) -> dict:
    db.update_run(state["run_id"], status="done")
    db.add_event(state["run_id"], "finish", "Run complete")
    return {}


def after_critic(state: ValidatorState) -> str:
    """The decision point: search again, or move on to scoring?"""
    has_gaps = bool(state["gaps"])
    loops_left = state["loop_count"] < MAX_LOOPS
    room_for_sources = len(state["sources"]) < MAX_SOURCES_TOTAL
    if has_gaps and loops_left and room_for_sources:
        return "prepare_retry"
    return "score"


def build_graph():
    builder = StateGraph(ValidatorState)

    builder.add_node("intake", safe("intake", intake_node))
    builder.add_node("recall", safe("recall", recall_node))
    builder.add_node("plan_research", safe("researcher", plan_research))
    builder.add_node("search_web", safe("researcher", search_web))
    builder.add_node("analyst", safe("analyst", analyst_node))
    builder.add_node("critic", safe("critic", critic_node))
    builder.add_node("prepare_retry", prepare_retry)
    builder.add_node("score", safe("scoring", score_node))
    builder.add_node("report", safe("reporter", report_node))
    builder.add_node("finish", finish_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "recall")
    builder.add_edge("recall", "plan_research")
    builder.add_edge("plan_research", "search_web")
    builder.add_edge("search_web", "analyst")
    builder.add_edge("analyst", "critic")

    # the loop: gaps send the work back to the Researcher
    builder.add_conditional_edges(
        "critic",
        after_critic,
        {"prepare_retry": "prepare_retry", "score": "score"},
    )
    builder.add_edge("prepare_retry", "plan_research")

    builder.add_edge("score", "report")
    builder.add_edge("report", "finish")
    builder.add_edge("finish", END)
    return builder.compile()


graph = build_graph()


def run_validator(run_id: str, idea_text: str) -> dict:
    """Run the whole agent and return the final state. The API will call this."""
    state = initial_state(run_id, idea_text)
    return graph.invoke(state, config={"recursion_limit": 60})