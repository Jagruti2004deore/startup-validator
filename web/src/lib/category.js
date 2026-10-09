export const CATEGORY_ORDER = [
  "competitor",
  "pricing",
  "market_size",
  "demand_signal",
  "recent_activity",
  "failure_or_risk",
  "differentiation_gap",
  "conflict_with_past_notes",
];

export const CATEGORY_LABEL = {
  competitor: "Competitors",
  pricing: "Pricing",
  market_size: "Market size",
  demand_signal: "Customer demand",
  recent_activity: "Recent activity",
  failure_or_risk: "Risks",
  differentiation_gap: "Differentiation",
  conflict_with_past_notes: "Your past decisions",
};

export function claimsByCategory(claims) {
  const result = {};
  for (const claim of claims) {
    (result[claim.category] ??= []).push(claim);
  }
  return result;
}