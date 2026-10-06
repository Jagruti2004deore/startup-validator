from typing import TypedDict, List, Dict, Any


class ValidatorState(TypedDict):
    """The agent's notebook, passed from step to step."""
    run_id: str
    idea_text: str
    profile: Dict[str, Any]       # the structured idea
    past_notes: List[str]         # similar notes from Pinecone
    queries: List[str]            # search queries for this round
    sources: List[Dict]           # {url, title, content}; the source number = position + 1
    claims: List[Dict]            # every claim made by the Analyst
    verified: List[Dict]          # claims that passed the Critic
    dropped: List[Dict]           # claims that failed, with a reason
    gaps: List[str]               # checklist items still missing
    loop_count: int               # how many times the Critic sent work back
    score: Dict[str, Any]         # checklist results
    verdict: str
    report: str


def initial_state(run_id: str, idea_text: str) -> ValidatorState:
    """A fresh, empty notebook for a new run."""
    return {
        "run_id": run_id,
        "idea_text": idea_text,
        "profile": {},
        "past_notes": [],
        "queries": [],
        "sources": [],
        "analyzed_count": 0,
        "claims": [],
        "verified": [],
        "dropped": [],
        "gaps": [],
        "loop_count": 0,
        "score": {},
        "verdict": "",
        "report": "",
    }