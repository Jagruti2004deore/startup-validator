export class ApiError extends Error {
  constructor(status, message = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const ACCESS = {
  title: "Access code needed",
  message: "Enter your access code to continue.",
  needsAccessCode: true,
};

/** Turn any failure into words a founder can act on. Never shows raw errors. */
export function friendlyError(err) {
  const status = err instanceof ApiError ? err.status : -1;
  switch (status) {
    case 401:
      return ACCESS;
    case 404:
      return {
        title: "We couldn't find this validation",
        message: "It may have been removed. Please start a new one.",
        needsAccessCode: false,
      };
    case 409:
      return {
        title: "A validation is already running",
        message: "Please wait for it to finish, then try again.",
        needsAccessCode: false,
      };
    case 422:
      return {
        title: "A little more detail, please",
        message: "Describe your idea in at least one full sentence.",
        needsAccessCode: false,
      };
    case 429:
      return {
        title: "Daily limit reached",
        message: "You've reached today's validation limit. Please try again tomorrow.",
        needsAccessCode: false,
      };
    case 0:
      return {
        title: "Can't reach the service",
        message:
          "Check your connection and try again. If the service was idle, it may need a minute to wake up.",
        needsAccessCode: false,
      };
    default:
      return {
        title: "Validation couldn't be completed",
        message: "Something went wrong while researching this idea. Please try again.",
        needsAccessCode: false,
      };
  }
}

/** Errors while saving or removing a founder memory. */
export function friendlyMemoryError(err) {
  const status = err instanceof ApiError ? err.status : -1;
  if (status === 401) return ACCESS;
  if (status === 0) return friendlyError(err);
  if (status === 422) {
    return {
      title: "Add a little more",
      message: "Write at least a short sentence so it's useful later.",
      needsAccessCode: false,
    };
  }
  if (status === 404) {
    return {
      title: "That memory is already gone",
      message: "Refresh the page to see your current memories.",
      needsAccessCode: false,
    };
  }
  return {
    title: "We couldn't update your memories",
    message: "Something went wrong. Please try again in a moment.",
    needsAccessCode: false,
  };
}

/** Errors while loading a list or a page. */
export function friendlyLoadError(err) {
  const status = err instanceof ApiError ? err.status : -1;
  if (status === 401) return ACCESS;
  if (status === 0) return friendlyError(err);
  return {
    title: "We couldn't load this page",
    message: "Please try again in a moment.",
    needsAccessCode: false,
  };
}

/** A run that ended as failed: pick a friendly message from its last system event. */
export function failedRunMessage(events) {
  const last = [...events].reverse().find((e) => e.node === "system");
  const text = (last?.message ?? "").toLowerCase();
  if (text.includes("limit") || text.includes("token")) {
    return {
      title: "Research allowance reached",
      message: "The daily research allowance has been used up. Please try again later.",
      needsAccessCode: false,
    };
  }
  return {
    title: "Validation couldn't be completed",
    message: "Something went wrong while researching this idea. Please try again.",
    needsAccessCode: false,
  };
}