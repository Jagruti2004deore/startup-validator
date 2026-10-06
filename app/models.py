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
    """The Critic's answer when checking one claim against one source."""
    supported: bool = Field(description="True only if the source text clearly supports the claim")
    evidence_quote: str = Field(
        description="Exact words copied from the source that support the claim, or an empty string"
    )


class NoteConflict(BaseModel):
    """How a past founder note relates to the new idea."""
    relevant: bool = Field(description="True only if a past note directly relates to this idea")
    claim_text: str = Field(
        description="One sentence on how the note relates (agrees, conflicts, or repeats a past rejection). Empty if not relevant"
    )
    note_quote: str = Field(
        description="Exact words copied from the past note that support the sentence. Empty if not relevant"
    )