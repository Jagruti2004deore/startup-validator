import { describe, expect, it } from "vitest";
import { checklistRows, insightCards, nextStep, signalCards, verdictSentence } from "./insights";

const KEYS = [
  "competitors", "pricing", "demand", "market_size",
  "recent_activity", "failure_or_risk", "differentiation_gap", "memory",
];
const items = (failed = []) =>
  KEYS.map((key) => ({
    key, label: key, needed: 1,
    found: failed.includes(key) ? 0 : 1,
    passed: !failed.includes(key),
  }));
const score = (over = {}) => ({
  verdict: "Promising", items: items(), competitors_found: 4, crowdedness: "medium",
  has_gap: true, has_demand: true, has_conflict: false, ...over,
});

describe("verdictSentence", () => {
  it("names what still needs validation when promising", () => {
    expect(verdictSentence(score({ items: items(["pricing"]) }))).toContain(
      "competitor pricing still needs validation",
    );
  });

  it("is simple when everything is verified", () => {
    expect(verdictSentence(score())).toContain("clear opening");
  });

  it("lists what holds a cautious verdict back", () => {
    const text = verdictSentence(score({ verdict: "Proceed with caution", has_gap: false, has_demand: false }));
    expect(text).toContain("no verified differentiation and no verified customer demand");
  });

  it("explains an unclear verdict", () => {
    const text = verdictSentence(score({ verdict: "Unclear: not enough verified evidence" }));
    expect(text).toMatch(/isn't enough verified evidence/);
  });
});

describe("checklistRows", () => {
  it("puts gaps last and links to evidence only where it exists", () => {
    const rows = checklistRows(score({ items: items(["pricing", "memory"]) }));
    expect(rows.slice(0, 6).every((r) => r.passed)).toBe(true);
    expect(rows.slice(6).every((r) => !r.passed)).toBe(true);
    expect(rows.find((r) => r.key === "competitors").category).toBe("competitor");
    expect(rows.find((r) => r.key === "memory").category).toBeNull();
    expect(rows.find((r) => r.key === "pricing").label).toBe("Competitor pricing incomplete");
  });
});

describe("nextStep", () => {
  it("follows the priority order", () => {
    expect(nextStep(score({ items: items(["pricing", "demand"]) })).key).toBe("demand");
  });

  it("puts a conflict with past decisions first", () => {
    expect(nextStep(score({ has_conflict: true, items: items(["demand"]) })).key).toBe("conflict");
  });

  it("is honest when nothing is missing", () => {
    expect(nextStep(score()).key).toBe("validated");
  });
});

describe("signalCards", () => {
  it("summarises a full result", () => {
    const cards = signalCards(score());
    expect(cards).toHaveLength(4);
    expect(cards.find((c) => c.key === "market").value).toBe("Medium competition");
    expect(cards.find((c) => c.key === "competitors").value).toBe("4 verified");
    expect(cards.find((c) => c.key === "demand").value).toBe("Evidence found");
    expect(cards.find((c) => c.key === "differentiation").value).toBe("Opportunity identified");
  });

  it("does not guess when data is missing", () => {
    const cards = signalCards(score({ crowdedness: "unknown", competitors_found: 0, has_demand: false, has_gap: false }));
    expect(cards.find((c) => c.key === "market").value).toBe("Not enough data");
    expect(cards.find((c) => c.key === "competitors").value).toBe("None verified");
  });
});

describe("insightCards", () => {
  it("says so when nothing was verified", () => {
    const cards = insightCards([], score({ competitors_found: 0, crowdedness: "unknown" }));
    expect(cards).toHaveLength(3);
    expect(cards[0].text).toBe("No competitors could be verified yet.");
    expect(cards[1].text).toMatch(/no differentiation opportunity/i);
    expect(cards[2].text).toMatch(/does not mean there are none/);
  });

  it("uses the real verified claims", () => {
    const verified = [
      { category: "market_size", text: "The market is large." },
      { category: "differentiation_gap", text: "Among the competitors found, none mention X." },
      { category: "failure_or_risk", text: "A rival shut down in 2025." },
    ];
    const cards = insightCards(verified, score());
    expect(cards[0].detail).toBe("The market is large.");
    expect(cards[1].text).toBe("Among the competitors found, none mention X.");
    expect(cards[2].text).toBe("A rival shut down in 2025.");
  });
});