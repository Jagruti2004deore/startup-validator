import { AccessCodePrompt } from "./AccessCodePrompt";
import { Button, Notice } from "./ui";

/** Shows a friendly error. `error` is the object returned by the friendly...Error helpers. */
export function ErrorPanel({ error, onRetry, onAccessSaved }) {
  if (error.needsAccessCode) return <AccessCodePrompt onSaved={onAccessSaved ?? onRetry} />;
  return (
    <Notice
      title={error.title}
      action={onRetry && <Button variant="secondary" onClick={onRetry}>Try again</Button>}
    >
      {error.message}
    </Notice>
  );
}