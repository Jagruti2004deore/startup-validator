from typing import List, Literal
from pydantic import BaseModel, Field

# The only kinds of claims the agents are allowed to make
ClaimCategory = Literal[
    "competitor",
    "pricing",
    "market_size",
    "demand_signal",
    "recent_activity",
    "failure_or_risk",
    "differentiation_gap",
    "conflict_with_past_notes",
]

# What the Critic may relabel a claim as (or "irrelevant" to drop it)
CheckCategory = Literal[
    "competitor",
    "pricing",
    "market_size",
    "demand_signal",
    "recent_activity",
    "failure_or_risk",
    "irrelevant",
]


class IdeaProfile(BaseModel):
    """The idea, turned into a clean structure."""
    name: str = Field(description="Short working name for the idea")
    problem: str = Field(description="The problem the idea solves, in one or two sentences")
    target_customer: str = Field(description="Who would pay for or use this")
    solution: str = Field(description="What the product does, in one or two sentences")
    geography: str = Field(default="not specified", description="Country or region, if mentioned")
    category: str = Field(description="Market category, for example edtech, fintech, health")


class QueryPlan(BaseModel):
    """Search queries for one research round."""
    queries: List[str] = Field(description="Distinct web search queries")


class Claim(BaseModel):
    """One factual statement, tied to its sources."""
    text: str = Field(description="One specific factual statement")
    category: ClaimCategory
    source_ids: List[int] = Field(description="Numbers of the sources that support this claim")


class ClaimList(BaseModel):
    claims: List[Claim]


class ClaimCheck(BaseModel):
    """The Critic's verdict on one claim and its source text."""
    supported: bool = Field(description="True only if the source text clearly states what the claim says")
    evidence_quote: str = Field(
        description="One continuous passage copied exactly from the source text that supports the claim. Empty if not supported"
    )
    best_category: CheckCategory = Field(
        description="The category that fits the claim best, or irrelevant if it is not useful evidence for this idea"
    )
    reason: str = Field(description="One short sentence explaining the verdict")


class NoteConflict(BaseModel):
    """How a past founder note relates to the new idea."""
    relevant: bool = Field(description="True only if a past note directly relates to this idea")
    claim_text: str = Field(
        description="One sentence on how the note relates (agrees, conflicts, or repeats a past rejection). Empty if not relevant"
    )
    note_quote: str = Field(
        description="Exact words copied from the past note that support the sentence. Empty if not relevant"
    )


class GapStatement(BaseModel):
    """The Critic's analysis of what verified competitors do not mention."""
    has_gap: bool = Field(description="True if at least one feature of the idea is not mentioned by any competitor fact")
    feature: str = Field(description="The founder's feature in 2 to 6 words. Empty if no gap")
    statement: str = Field(description="One sentence starting with 'Among the competitors found,'. Empty if no gap")
    based_on: List[int] = Field(description="Numbers of the competitor facts that were compared")