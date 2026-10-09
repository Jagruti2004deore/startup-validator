export const STAGES = [
  "Understanding the opportunity",
  "Researching competitors",
  "Checking market evidence",
  "Reviewing risks",
  "Preparing your validation report",
];

// The server's internal step names, mapped to what a founder cares about.
const NODE_STAGE = {
  intake: 0,
  recall: 0,
  researcher: 1,
  analyst: 2,
  critic: 2,
  scoring: 3,
  reporter: 4,
  finish: 4,
};

/** Returns "done", "active" or "waiting" for each stage. */
export function stageStates(nodes, status) {
  if (status === "done") return STAGES.map(() => "done");
  let current = 0;
  for (const node of nodes) {
    const index = NODE_STAGE[node];
    if (index !== undefined && index > current) current = index;
  }
  return STAGES.map((_, i) => (i < current ? "done" : i === current ? "active" : "waiting"));
}

/** True while the agent is searching again to fill gaps in the evidence. */
export function isDiggingDeeper(nodes) {
  const lastLoop = nodes.lastIndexOf("loop");
  if (lastLoop === -1) return false;
  return !nodes.slice(lastLoop).some((n) => n === "scoring" || n === "reporter" || n === "finish");
}