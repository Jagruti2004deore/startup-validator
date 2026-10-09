const LABELS = {
  number_not_in_source: "A number in the claim did not match the source",
  name_not_in_source: "A company named in the claim could not be confirmed in the source",
  source_number_does_not_exist: "The claim pointed to a source that does not exist",
  no_source_cited: "The claim had no source",
  not_supported_by_source: "The source did not support the claim",
  quote_not_found_in_source: "The supporting quote was not found in the source",
  not_relevant_to_idea: "True, but not relevant evidence for this idea",
  not_a_market_figure: "Not a market size or growth figure",
  pricing_for_unverified_competitor: "Pricing for a company not verified as a competitor",
  note_quote_not_found: "The quoted text was not found in your memories",
  feature_already_offered: "The differentiation was already offered by a competitor",
  check_failed: "The check could not be completed",
};

export function reasonLabel(reason) {
  const code = String(reason ?? "").split(":")[0].trim();
  if (!code) return "Other";
  if (LABELS[code]) return LABELS[code];
  const text = code.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Count rejected claims by friendly reason, biggest group first. */
export function groupReasons(dropped) {
  const counts = new Map();
  for (const claim of dropped) {
    const label = reasonLabel(claim.drop_reason);
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);
}