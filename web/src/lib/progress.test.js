import { describe, expect, it } from "vitest";
import { isDiggingDeeper, stageStates } from "./progress";

describe("stageStates", () => {
  it("starts at the first stage", () => {
    expect(stageStates([], "running")).toEqual(["active", "waiting", "waiting", "waiting", "waiting"]);
  });

  it("moves forward as steps happen", () => {
    expect(stageStates(["intake", "recall", "researcher", "analyst"], "running")).toEqual([
      "done", "done", "active", "waiting", "waiting",
    ]);
  });

  it("never moves backward when the agent searches again", () => {
    const nodes = ["intake", "researcher", "analyst", "critic", "loop", "researcher"];
    expect(stageStates(nodes, "running")).toEqual(["done", "done", "active", "waiting", "waiting"]);
  });

  it("marks everything done when finished", () => {
    expect(stageStates([], "done")).toEqual(["done", "done", "done", "done", "done"]);
  });
});

describe("isDiggingDeeper", () => {
  it("is false before any retry", () => {
    expect(isDiggingDeeper(["intake", "researcher", "critic"])).toBe(false);
  });

  it("is true while searching again", () => {
    expect(isDiggingDeeper(["critic", "loop", "researcher"])).toBe(true);
  });

  it("is false once scoring starts", () => {
    expect(isDiggingDeeper(["critic", "loop", "researcher", "critic", "scoring"])).toBe(false);
  });
});