import { describe, expect, it } from "vitest";
import { groupReasons, reasonLabel } from "./reasons";

describe("reasonLabel", () => {
  it("explains a known reason and ignores the detail", () => {
    expect(reasonLabel("number_not_in_source: 49")).toBe("A number in the claim did not match the source");
  });

  it("makes an unknown reason readable", () => {
    expect(reasonLabel("some_new_reason")).toBe("Some new reason");
  });

  it("handles a missing reason", () => {
    expect(reasonLabel(null)).toBe("Other");
  });
});

describe("groupReasons", () => {
  it("counts by friendly reason, biggest first", () => {
    const dropped = [
      { drop_reason: "name_not_in_source: Zoom" },
      { drop_reason: "not_supported_by_source: nope" },
      { drop_reason: "not_supported_by_source: nope again" },
    ];
    const groups = groupReasons(dropped);
    expect(groups[0]).toEqual({ label: "The source did not support the claim", count: 2 });
    expect(groups).toHaveLength(2);
  });
});