import { describe, expect, it } from "vitest";
import {
  buildCitationMap, buildSourceList, citeNumbers, parseReport, splitCitations,
} from "./reportParse";

const REPORT = `# Study Buddy: startup idea validation

## Summary
Alpha is a rival [1]. Beta is one too [2].

## Key findings
- something

## Sources
[1] Source Five - https://example.com/5  
[2] Top apps - 2026 - https://example.com/3  
`;

describe("parseReport", () => {
  it("reads the summary and the sources", () => {
    const parsed = parseReport(REPORT);
    expect(parsed.summary).toBe("Alpha is a rival [1]. Beta is one too [2].");
    expect(parsed.sources).toHaveLength(2);
    expect(parsed.sources[0]).toEqual({ n: 1, title: "Source Five", url: "https://example.com/5" });
  });

  it("keeps dashes inside titles", () => {
    expect(parseReport(REPORT).sources[1].title).toBe("Top apps - 2026");
  });

  it("copes with an empty report", () => {
    expect(parseReport("")).toEqual({ summary: "", sources: [] });
  });
});

describe("splitCitations", () => {
  it("separates text from citation numbers", () => {
    expect(splitCitations("Great [1][2].")).toEqual([
      { type: "text", value: "Great " },
      { type: "cite", value: 1 },
      { type: "cite", value: 2 },
      { type: "text", value: "." },
    ]);
  });
});

describe("citation numbers", () => {
  const rows = [
    { source_no: 5, url: "https://example.com/5", content: "Alpha   offers study groups for students." },
    { source_no: 3, url: "https://example.com/3/", content: "" },
    { source_no: 9, url: "https://example.com/never-cited", content: "x" },
  ];

  it("maps database numbers to report numbers", () => {
    const parsed = parseReport(REPORT);
    const map = buildCitationMap(parsed.sources, rows);
    expect(map).toEqual({ 5: 1, 3: 2 });
    expect(citeNumbers({ source_nos: [3, 5, 9] }, map)).toEqual([1, 2]);
  });

  it("builds the source list with website names and a short description", () => {
    const parsed = parseReport(REPORT);
    const list = buildSourceList(parsed.sources, rows);
    expect(list[0].domain).toBe("example.com");
    expect(list[0].snippet).toBe("Alpha offers study groups for students.");
    expect(list[1].snippet).toBe("");
  });
});