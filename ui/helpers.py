from urllib.parse import urlparse

TOTAL_ITEMS = 8  # checklist items, as in app/scoring.py

REASON_LABELS = {
    "number_not_in_source": "A number in the claim was not in the source",
    "name_not_in_source": "A company name in the claim was not in the source",
    "source_number_does_not_exist": "The claim cited a source that does not exist",
    "no_source_cited": "The claim cited no source",
    "not_supported_by_source": "The source did not support the claim",
    "quote_not_found_in_source": "The supporting quote was not found in the source",
    "not_relevant_to_idea": "True, but not useful evidence for this idea",
    "not_a_market_figure": "Not a market size or growth figure",
    "pricing_for_unverified_competitor": "Pricing for a company not verified as a competitor",
    "note_quote_not_found": "The quoted note text was not found in your notes",
    "feature_already_offered": "The gap feature is already offered by a competitor",
    "check_failed": "The check could not be completed",
}

CATEGORY_LABELS = {
    "competitor": "Competitor",
    "pricing": "Pricing",
    "market_size": "Market size",
    "demand_signal": "Customer demand",
    "recent_activity": "Recent activity",
    "failure_or_risk": "Failure or risk",
    "differentiation_gap": "Differentiation gap (analysis)",
    "conflict_with_past_notes": "Your past notes",
}

NODE_ICONS = {
    "intake": "🧠", "recall": "🗂️", "researcher": "🌐", "analyst": "📖",
    "critic": "⚖️", "loop": "🔁", "scoring": "🧮", "reporter": "📝",
    "finish": "✅", "system": "⚠️",
}


def verdict_kind(verdict) -> str:
    """Which Streamlit banner to use: success, warning, error or info."""
    if not verdict:
        return "info"
    if verdict == "Promising":
        return "success"
    if verdict == "Proceed with caution":
        return "warning"
    if verdict == "Risky":
        return "error"
    return "info"  # "Unclear: not enough verified evidence"


def reason_label(reason) -> str:
    if not reason:
        return "other"
    code = str(reason).split(":")[0].strip()
    return REASON_LABELS.get(code, code.replace("_", " "))


def short(text, limit: int = 90) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def domain(url) -> str:
    return urlparse(url or "").netloc.lower().removeprefix("www.")


def claim_rows(claims: list, sources: list) -> list:
    """Table rows for verified claims. Sources are shown as website names."""
    by_no = {s["source_no"]: s.get("url", "") for s in sources}
    rows = []
    for c in claims:
        domains = sorted({domain(by_no[n]) for n in c.get("source_nos", []) if n in by_no})
        rows.append({
            "Category": CATEGORY_LABELS.get(c.get("category"), c.get("category", "")),
            "Claim": c.get("text", ""),
            "Sources": ", ".join(domains) or "-",
        })
    return rows


def dropped_rows(claims: list) -> list:
    return [
        {
            "Category": CATEGORY_LABELS.get(c.get("category"), c.get("category", "")),
            "Claim": c.get("text", ""),
            "Why it was removed": reason_label(c.get("drop_reason")),
        }
        for c in claims
    ]


def source_lines(sources: list) -> list:
    lines = []
    for s in sources:
        title = (s.get("title") or "Untitled").replace("[", "(").replace("]", ")")
        lines.append(f"{s['source_no']}. [{title}]({s.get('url', '')})")
    return lines