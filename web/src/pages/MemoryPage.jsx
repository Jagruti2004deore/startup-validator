import { useState } from "react";
import { Brain, Plus, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { ErrorPanel } from "../components/ErrorPanel";
import { LoadingBlock } from "../components/LoadingBlock";
import { Button, Card } from "../components/ui";
import { useLoader } from "../hooks/useLoader";
import { friendlyLoadError, friendlyMemoryError } from "../lib/errors";
import { formatDate } from "../lib/format";

const MIN_LENGTH = 5;
const MAX_LENGTH = 4000;

const loadNotes = () => api.listNotes();

export default function MemoryPage() {
  const [version, setVersion] = useState(0);
  const state = useLoader(loadNotes, version);
  const notes = state.phase === "ready" ? state.data : [];

  const [composing, setComposing] = useState(false);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [confirmId, setConfirmId] = useState(null);

  const reload = () => setVersion((n) => n + 1);

  async function save() {
    if (text.trim().length < MIN_LENGTH || saving) return;
    setSaving(true);
    setFormError(null);
    try {
      await api.addNote(text.trim());
      setText("");
      setComposing(false);
      reload();
    } catch (error) {
      setFormError(friendlyMemoryError(error));
    } finally {
      setSaving(false);
    }
  }

  async function remove(id) {
    setFormError(null);
    try {
      await api.deleteNote(id);
      setConfirmId(null);
      reload();
    } catch (error) {
      setConfirmId(null);
      setFormError(friendlyMemoryError(error));
    }
  }

  const openComposer = () => {
    setFormError(null);
    setComposing(true);
  };

  return (
    <div className="animate-fade-up max-w-3xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Founder Memory</h1>
          <p className="mt-1 text-muted">
            Your previous decisions help the validator understand what matters to you.
          </p>
        </div>
        {!composing && notes.length > 0 && (
          <Button onClick={openComposer}>
            <Plus className="h-4 w-4" /> Add Memory
          </Button>
        )}
      </div>
      <p className="mt-3 text-sm text-muted">
        The validator can use these memories when evaluating future ideas.
      </p>

      {composing && (
        <Card className="animate-fade-up mt-6 p-5">
          <label htmlFor="memory" className="block text-sm font-medium">
            What should the validator remember?
          </label>
          <textarea
            id="memory"
            value={text}
            maxLength={MAX_LENGTH}
            rows={4}
            autoFocus
            onChange={(event) => setText(event.target.value)}
            placeholder="e.g. I rejected a flashcard app because the market was too crowded."
            className="mt-3 w-full resize-y rounded-xl border border-line px-4 py-3 text-[15px] leading-relaxed outline-none placeholder:text-stone-400 focus:border-accent"
          />
          <div className="mt-4 flex items-center gap-3">
            <Button onClick={save} disabled={text.trim().length < MIN_LENGTH || saving}>
              {saving ? "Saving..." : "Save memory"}
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setComposing(false);
                setText("");
                setFormError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </Card>
      )}

      {formError && (
        <div className="mt-4">
          <ErrorPanel
            error={formError}
            onAccessSaved={() => {
              setFormError(null);
              reload();
            }}
          />
        </div>
      )}

      <div className="mt-8">
        {state.phase === "loading" && <LoadingBlock blocks={2} />}
        {state.phase === "error" && (
          <ErrorPanel error={friendlyLoadError(state.error)} onRetry={reload} />
        )}

        {state.phase === "ready" && notes.length === 0 && !composing && (
          <EmptyState
            icon={Brain}
            title="No founder memories yet."
            text="Save decisions and preferences that should influence future validations."
            action={<Button onClick={openComposer}>Add your first memory →</Button>}
          />
        )}

        {state.phase === "ready" && notes.length > 0 && (
          <ul className="space-y-3">
            {notes.map((note) => (
              <li key={note.id}>
                <Card className="p-5">
                  <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{note.text}</p>
                  <div className="mt-3 flex items-center justify-between gap-3">
                    <span className="text-sm text-muted">{formatDate(note.created_at, true)}</span>
                    {confirmId === note.id ? (
                      <span className="flex items-center gap-3 text-sm">
                        <span className="text-muted">Remove this memory?</span>
                        <button
                          type="button"
                          onClick={() => remove(note.id)}
                          className="font-medium text-risk hover:underline"
                        >
                          Remove
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmId(null)}
                          className="text-muted hover:text-ink"
                        >
                          Keep
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        aria-label="Remove memory"
                        onClick={() => setConfirmId(note.id)}
                        className="rounded p-1.5 text-stone-400 transition-colors hover:bg-stone-100 hover:text-risk"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}