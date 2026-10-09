export function formatDate(iso, long = false) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-US", {
    month: long ? "long" : "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function domainOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export function truncate(text, max) {
  const clean = (text ?? "").trim();
  if (clean.length <= max) return clean;
  return clean.slice(0, max - 1).trimEnd() + "…";
}

export function plural(count, one, many = `${one}s`) {
  return count === 1 ? one : many;
}

/** Only web links are allowed. Anything else (for example javascript:) becomes empty. */
export function safeUrl(url) {
  return /^https?:\/\//i.test(url ?? "") ? url : "";
}

export function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}