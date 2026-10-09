const LABELS = {
  intake: "Understanding the idea",
  recall: "Checking your memories",
  researcher: "Researching",
  analyst: "Reading sources",
  critic: "Verifying claims",
  loop: "Searching again",
  scoring: "Scoring",
  reporter: "Writing the report",
  finish: "Finished",
  system: "Notice",
};

export const stageLabel = (node) => LABELS[node] ?? "Step";