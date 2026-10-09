import { ApiError } from "../lib/errors";

const BASE = String(import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const KEY_STORAGE = "sv_access_code";

export const accessCode = {
  get: () => localStorage.getItem(KEY_STORAGE) ?? "",
  set: (value) => localStorage.setItem(KEY_STORAGE, value.trim()),
  clear: () => localStorage.removeItem(KEY_STORAGE),
};

async function request(method, path, body) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const code = accessCode.get();
  if (code) headers["X-API-Key"] = code;

  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network");
  }

  if (!response.ok) {
    let detail = "";
    try {
      const data = await response.json();
      detail = typeof data.detail === "string" ? data.detail : "";
    } catch {
      // the body was not JSON; the status code is enough
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export const api = {
  startValidation: (idea) => request("POST", "/validate", { idea }),
  getRun: (runId, after = 0) => request("GET", `/runs/${runId}?after=${after}`),
  listRuns: (limit = 50) => request("GET", `/runs?limit=${limit}`),
  getReport: (runId) => request("GET", `/runs/${runId}/report`),
  listNotes: () => request("GET", "/notes"),
  addNote: (text) => request("POST", "/notes", { text }),
  deleteNote: (id) => request("DELETE", `/notes/${id}`),
};