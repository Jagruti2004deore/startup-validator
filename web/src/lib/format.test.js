import { describe, expect, it } from "vitest";
import { domainOf, formatDate, plural, safeUrl, truncate } from "./format";

describe("formatDate", () => {
  it("formats a short date", () => {
    expect(formatDate("2026-10-07T12:52:32")).toBe("Oct 7, 2026");
  });

  it("formats a long date", () => {
    expect(formatDate("2026-10-07T12:52:32", true)).toBe("October 7, 2026");
  });

  it("returns nothing for a missing or broken date", () => {
    expect(formatDate(null)).toBe("");
    expect(formatDate("not a date")).toBe("");
  });
});

describe("helpers", () => {
  it("reads the website name", () => {
    expect(domainOf("https://www.example.com/a/b")).toBe("example.com");
    expect(domainOf("nonsense")).toBe("");
  });

  it("shortens long text", () => {
    expect(truncate("short", 10)).toBe("short");
    expect(truncate("a".repeat(30), 10).length).toBe(10);
  });

  it("chooses singular or plural", () => {
    expect(plural(1, "claim")).toBe("claim");
    expect(plural(2, "claim")).toBe("claims");
  });

  it("only allows web links", () => {
    expect(safeUrl("https://example.com")).toBe("https://example.com");
    expect(safeUrl("javascript:alert(1)")).toBe("");
  });
});