export const CHECK_LABELS = {
  competitors: ["Direct competitors identified", "Direct competitors not verified"],
  pricing: ["Competitor pricing found", "Competitor pricing incomplete"],
  demand: ["Customer demand evidence", "Customer demand not verified"],
  market_size: ["Market size evidence", "Market size not verified"],
  recent_activity: ["Recent market activity", "No recent market activity verified"],
  failure_or_risk: ["Risk evidence", "No documented risk verified"],
  differentiation_gap: ["Differentiation opportunity", "No differentiation opportunity verified"],
  memory: ["Founder history checked", "Founder history not available"],
};

// Which kind of verified claim backs each checklist item (used for "View evidence").
export const EVIDENCE_CATEGORY = {
  competitors: "competitor",
  pricing: "pricing",
  demand: "demand_signal",
  market_size: "market_size",
  recent_activity: "recent_activity",
  failure_or_risk: "failure_or_risk",
  differentiation_gap: "differentiation_gap",
};

const NEEDS = {
  competitors: "competitor evidence",
  pricing: "competitor pricing",
  demand: "customer demand",
  market_size: "market size",
  recent_activity: "recent market activity",
  failure_or_risk: "risks",
  differentiation_gap: "differentiation",
  memory: "your past decisions",
};

export function verdictKind(verdict) {
  if (!verdict) return "pending";
  if (verdict.startsWith("Unclear")) return "unclear";
  if (verdict === "Promising") return "promising";
  if (verdict === "Proceed with caution") return "caution";
  if (verdict === "Risky") return "risky";
  return "pending";
}

function joinList(items) {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

/** One sentence under the verdict, built from the rule-based score. */
export function verdictSentence(score) {
  if (!score) return "";
  const kind = verdictKind(score.verdict);
  const missing = score.items.filter((i) => !i.passed && i.key !== "memory");

  if (kind === "promising") {
    if (missing.length) {
      return `Verified evidence points to an opening in this market, but ${NEEDS[missing[0].key]} still needs validation.`;
    }
    return "Verified evidence points to a clear opening in this market.";
  }
  if (kind === "caution") {
    const blockers = [];
    if (!score.has_gap) blockers.push("no verified differentiation");
    if (!score.has_demand) blockers.push("no verified customer demand");
    if (score.crowdedness === "high") blockers.push("a crowded market");
    if (score.has_conflict) blockers.push("a conflict with your past decisions");
    if (blockers.length) return `Some evidence is in place, but there is ${joinList(blockers)}.`;
    return "Some evidence is in place, but not enough to call this promising.";
  }
  if (kind === "risky") {
    return "The market looks crowded, and no clear way to stand out was verified.";
  }
  if (kind === "unclear") {
    return "There isn't enough verified evidence to judge this idea yet.";
  }
  return "";
}

/** The checklist as plain-language rows. Verified items first, gaps last. */
export function checklistRows(score) {
  const rows = score.items.map((item) => ({
    key: item.key,
    passed: item.passed,
    found: item.found,
    needed: item.needed,
    label: CHECK_LABELS[item.key]?.[item.passed ? 0 : 1] ?? item.label,
    category: EVIDENCE_CATEGORY[item.key] ?? null,
  }));
  return [...rows.filter((r) => r.passed), ...rows.filter((r) => !r.passed)];
}

export function signalCards(score) {
  const crowd =
    {
      low: ["Low competition", "good"],
      medium: ["Medium competition", "caution"],
      high: ["High competition", "risk"],
    }[score.crowdedness] ?? ["Not enough data", "neutral"];
  const n = score.competitors_found;
  return [
    { key: "market", label: "Market", value: crowd[0], tone: crowd[1] },
    {
      key: "competitors",
      label: "Competitors",
      value: n ? `${n} verified` : "None verified",
      tone: n >= 3 ? "good" : n > 0 ? "caution" : "neutral",
    },
    {
      key: "demand",
      label: "Demand",
      value: score.has_demand ? "Evidence found" : "Not verified",
      tone: score.has_demand ? "good" : "caution",
    },
    {
      key: "differentiation",
      label: "Differentiation",
      value: score.has_gap ? "Opportunity identified" : "Not verified",
      tone: score.has_gap ? "good" : "caution",
    },
  ];
}

/** Market, opportunity and risk, taken from real verified claims. Nothing is invented. */
export function insightCards(verified, score) {
  const first = (category) => verified.find((c) => c.category === category);
  const n = score.competitors_found;
  const market =
    n === 0
      ? "No competitors could be verified yet."
      : `Competition is ${score.crowdedness} with ${n} verified ${n === 1 ? "competitor" : "competitors"}. The real number can only be higher.`;
  const size = first("market_size");
  const gap = first("differentiation_gap");
  const risk = first("failure_or_risk");
  return [
    { key: "market", label: "Market", text: market, detail: size?.text ?? "" },
    {
      key: "opportunity",
      label: "Opportunity",
      text: gap?.text ?? "No differentiation opportunity could be verified.",
      detail: gap ? "Analysis based on verified competitors, not a statement from a source." : "",
    },
    {
      key: "risk",
      label: "Risk",
      text: risk?.text ?? "No specific risks were verified, which does not mean there are none.",
      detail: "",
    },
  ];
}

// Fixed advice, chosen by rule. It is not generated and does not claim any facts.
const NEXT = {
  conflict:
    "Revisit your earlier decision. Your saved memories conflict with this idea, so decide what has changed since then.",
  demand:
    "Talk to people in your target customer group. Ask how they deal with this problem today and what they would change, to find real evidence of demand.",
  pricing:
    "Validate willingness to pay. Ask target customers what they would pay and what they pay for alternatives today, since competitor pricing could not be verified.",
  competitors:
    "Map what your customers use today. Ask them which tools or workarounds they rely on, because few direct competitors could be verified.",
  market_size:
    "Size the opportunity yourself. Estimate how many target customers exist and what they might spend, since no market figure could be verified.",
  differentiation_gap:
    "Sharpen your differentiation. Compare your idea feature by feature with the closest alternatives, because no clear gap was verified.",
  failure_or_risk:
    "Look for why similar products struggled. Search for shutdowns in this space and check whether the same risks apply to you.",
  recent_activity:
    "Check for recent momentum. Look for launches, funding or news in this space to see whether interest is growing.",
  validated:
    "Test the assumptions behind this research with a few real customers before you build. Research cannot replace talking to them.",
};
const PRIORITY = [
  "demand", "pricing", "competitors", "market_size",
  "differentiation_gap", "failure_or_risk", "recent_activity",
];

export function nextStep(score) {
  if (score.has_conflict) {
    return { key: "conflict", text: NEXT.conflict, basis: "Your saved memories conflict with this idea." };
  }
  const failed = score.items.filter((i) => !i.passed).map((i) => i.key);
  for (const key of PRIORITY) {
    if (failed.includes(key)) {
      return {
        key,
        text: NEXT[key],
        basis: `Chosen from the first thing the research could not verify: ${CHECK_LABELS[key][1].toLowerCase()}.`,
      };
    }
  }
  return { key: "validated", text: NEXT.validated, basis: "Every checklist item was verified." };
}