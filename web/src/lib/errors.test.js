import { describe, expect, it } from "vitest";
import {
  ApiError, failedRunMessage, friendlyError, friendlyLoadError, friendlyMemoryError,
} from "./errors";

describe("friendlyError", () => {
  it("asks for an access code on 401", () => {
    expect(friendlyError(new ApiError(401)).needsAccessCode).toBe(true);
  });

  it("explains a run already in progress", () => {
    expect(friendlyError(new ApiError(409)).title).toMatch(/already running/i);
  });

  it("explains the daily limit", () => {
    expect(friendlyError(new ApiError(429)).message).toMatch(/tomorrow/i);
  });

  it("explains a network failure", () => {
    expect(friendlyError(new ApiError(0)).title).toMatch(/can't reach/i);
  });

  it("never leaks raw error text", () => {
    const text = JSON.stringify(friendlyError(new ApiError(500, "Traceback: KeyError in nodes.py")));
    expect(text).not.toMatch(/traceback|keyerror|nodes\.py/i);
  });
});

describe("failedRunMessage", () => {
  it("recognises the daily allowance", () => {
    const events = [{ node: "system", message: "The daily AI token limit is used up. Try again later." }];
    expect(failedRunMessage(events).title).toMatch(/allowance/i);
  });

  it("falls back to a generic message", () => {
    const events = [{ node: "system", message: "The run stopped with an error: boom" }];
    expect(failedRunMessage(events).message).not.toMatch(/boom/);
  });
});

describe("friendlyMemoryError", () => {
  it("asks for more text on 422", () => {
    expect(friendlyMemoryError(new ApiError(422)).title).toMatch(/more/i);
  });

  it("never leaks raw error text", () => {
    const text = JSON.stringify(friendlyMemoryError(new ApiError(502, "Pinecone index failure")));
    expect(text).not.toMatch(/pinecone|index/i);
  });
});

describe("friendlyLoadError", () => {
  it("asks for an access code on 401", () => {
    expect(friendlyLoadError(new ApiError(401)).needsAccessCode).toBe(true);
  });

  it("uses plain words otherwise", () => {
    expect(friendlyLoadError(new ApiError(500, "boom")).message).not.toMatch(/boom/);
  });
});