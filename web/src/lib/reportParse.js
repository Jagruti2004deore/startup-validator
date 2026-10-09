import { domainOf, truncate } from "./format";

const SOURCE_LINE = /^\[(\d+)\]\s+(.+?)\s+-\s+(https?:\/\/\S+)\s*$/;

function sectionText(markdown, heading) {
  const lines = markdown.split(/\r?\n/);
  const start = lines.findIndex((l) => l.trim().toLowerCase() === `## ${heading}`.toLowerCase());
  if (start === -1) return "";
  const body = [];
  for (let i = start + 1; i < lines.length; i += 1) {
    if (lines[i].startsWith("## ")) break;
    body.push(lines[i]);
  }
  return body.join("\n").trim();
}

/** Reads the summary and the numbered source list out of the saved report. */
export function parseReport(markdown) {
  const text = markdown || "";
  const sources = [];
  for (const line of sectionText(text, "Sources").split("\n")) {
    const match = line.trim().match(SOURCE_LINE);
    if (match) sources.push({ n: Number(match[1]), title: match[2], url: match[3] });
  }
  return { summary: sectionText(text, "Summary"), sources };
}

/** Splits "Great [1][2]." into text and citation pieces. */
export function splitCitations(text) {
  const parts = [];
  let last = 0;
  for (const match of text.matchAll(/\[(\d+)\]/g)) {
    if (match.index > last) parts.push({ type: "text", value: text.slice(last, match.index) });
    parts.push({ type: "cite", value: Number(match[1]) });
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push({ type: "text", value: text.slice(last) });
  return parts;
}

const normUrl = (url) => (url ?? "").trim().replace(/\/$/, "").toLowerCase();

/** Maps a database source number to the number used inside the report. */
export function buildCitationMap(parsedSources, rows) {
  const byUrl = new Map(parsedSources.map((s) => [normUrl(s.url), s.n]));
  const map = {};
  for (const row of rows) {
    const n = byUrl.get(normUrl(row.url));
    if (n) map[row.source_no] = n;
  }
  return map;
}

export function citeNumbers(claim, map) {
  const numbers = (claim.source_nos || []).map((no) => map[no]).filter(Boolean);
  return [...new Set(numbers)].sort((a, b) => a - b);
}

export function citeNumbersAll(claims, map) {
  const numbers = claims.flatMap((claim) => citeNumbers(claim, map));
  return [...new Set(numbers)].sort((a, b) => a - b);
}

export function buildSourceList(parsedSources, rows) {
  const byUrl = new Map(rows.map((r) => [normUrl(r.url), r]));
  return parsedSources.map((s) => {
    const row = byUrl.get(normUrl(s.url));
    const snippet = row?.content ? truncate(row.content.replace(/\s+/g, " "), 180) : "";
    return { ...s, domain: domainOf(s.url), snippet };
  });
}