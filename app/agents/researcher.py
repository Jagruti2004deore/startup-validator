from urllib.parse import urlparse

from tavily import TavilyClient

from app import db
from app.config import (
    TAVILY_API_KEY, RESULTS_PER_QUERY, MAX_CHARS_PER_SOURCE, MAX_SOURCES_TOTAL,
    MAX_PER_DOMAIN, GAP_ROUND_MAX_QUERIES, EXCLUDE_DOMAINS,
)
from app.llm_utils import ask_structured, get_llm
from app.models import QueryPlan
from app.prompts import PLAN_RESEARCH_PROMPT
from app.state import ValidatorState
from app.utils import today_note, clean_text

_tavily = TavilyClient(api_key=TAVILY_API_KEY)

# angle key -> what to look for. The keys match the claim categories.
ANGLES = {
    "competitor": "direct competitors and alternatives",
    "pricing": "how much competitors charge",
    "market_size": "market size or growth figures",
    "demand_signal": "evidence that customers have this problem (complaints, surveys, demand)",
    "recent_activity": "recent news, funding or product launches in this space",
    "failure_or_risk": "startups in this space that failed or shut down, and the main risks",
}


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _norm_url(url: str) -> str:
    """Treat 'site.com/a/' and 'site.com/a#top' as the same page."""
    return url.split("#")[0].rstrip("/").lower()


def _angles_for(state: ValidatorState) -> list:
    """First round: every angle. Later rounds: only the gaps the Critic found."""
    gaps = [g for g in state.get("gaps", []) if g in ANGLES]
    if state["loop_count"] > 0 and gaps:
        return gaps[:GAP_ROUND_MAX_QUERIES]
    return list(ANGLES)


# ---------- Node: plan the searches ----------
def plan_research(state: ValidatorState) -> dict:
    angles = _angles_for(state)
    p = state["profile"]
    angle_lines = "\n".join(f"{i}. {ANGLES[a]}" for i, a in enumerate(angles, start=1))
    old = "\n".join(f"- {q}" for q in state["queries"]) or "none"

    prompt = today_note() + PLAN_RESEARCH_PROMPT.format(
        name=p["name"], problem=p["problem"], solution=p["solution"],
        target_customer=p["target_customer"], geography=p["geography"],
        category=p["category"], angles=angle_lines, old_queries=old,
    )
    plan = ask_structured(get_llm(), prompt, QueryPlan)

    queries = [clean_text(q).strip() for q in plan.queries if q.strip()][:len(angles)]
    if not queries:
        queries = [f"{p['name']} competitors"]  # fallback so the run never stalls

    db.add_event(
        state["run_id"], "researcher",
        f"Planned {len(queries)} search(es) for: {', '.join(angles)}",
    )
    return {"queries": queries}


# ---------- Node: search the web ----------
def search_web(state: ValidatorState) -> dict:
    sources = list(state["sources"])
    seen_urls = {_norm_url(s["url"]) for s in sources}
    domain_count = {}
    for s in sources:
        d = _domain(s["url"])
        domain_count[d] = domain_count.get(d, 0) + 1

    added = 0
    for query in state["queries"]:
        if len(sources) >= MAX_SOURCES_TOTAL:
            break
        try:
            response = _tavily.search(
                query,
                max_results=RESULTS_PER_QUERY,
                exclude_domains=EXCLUDE_DOMAINS,
            )
        except Exception as e:
            print(f"  (search failed for '{query}': {e})")
            db.add_event(state["run_id"], "researcher", f"A search failed: {query}")
            continue  # one bad search must not kill the run

        for item in response.get("results", []):
            url = item.get("url")
            if not url or len(sources) >= MAX_SOURCES_TOTAL:
                continue
            key, dom = _norm_url(url), _domain(url)
            if key in seen_urls or domain_count.get(dom, 0) >= MAX_PER_DOMAIN:
                continue  # skip duplicates and over-represented sites
            seen_urls.add(key)
            domain_count[dom] = domain_count.get(dom, 0) + 1
            sources.append({
                "url": url,
                "title": clean_text(item.get("title") or "Untitled"),
                "content": clean_text(item.get("content") or "")[:MAX_CHARS_PER_SOURCE],
                "query": query,
            })
            added += 1

    db.save_sources(state["run_id"], sources)
    db.add_event(
        state["run_id"], "researcher",
        f"Added {added} new source(s), {len(sources)} in total",
    )
    return {"sources": sources}