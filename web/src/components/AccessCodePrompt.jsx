import { useState } from "react";
import { KeyRound } from "lucide-react";
import { accessCode } from "../api/client";
import { Button, Card } from "./ui";

export function AccessCodePrompt({ onSaved }) {
  const [value, setValue] = useState("");

  return (
    <Card className="animate-fade-up p-5">
      <div className="flex items-start gap-3">
        <KeyRound className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
        <div className="min-w-0 flex-1">
          <p className="font-medium">Access code needed</p>
          <p className="mt-1 text-sm text-muted">Enter the access code you were given to continue.</p>
          <form
            className="mt-4 flex flex-col gap-2 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              if (value.trim()) {
                accessCode.set(value);
                onSaved();
              }
            }}
          >
            <input
              type="password"
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Access code"
              autoComplete="off"
              className="w-full rounded-lg border border-line px-3 py-2.5 text-sm outline-none focus:border-accent sm:max-w-xs"
            />
            <Button type="submit" disabled={!value.trim()}>
              Continue
            </Button>
          </form>
        </div>
      </div>
    </Card>
  );
}