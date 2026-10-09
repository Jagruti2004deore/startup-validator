import { useState } from "react";
import { accessCode } from "../api/client";
import { Button, Card } from "../components/ui";

export default function SettingsPage() {
  const [saved, setSaved] = useState(Boolean(accessCode.get()));
  const [value, setValue] = useState("");
  const [message, setMessage] = useState("");

  function save(event) {
    event.preventDefault();
    if (!value.trim()) return;
    accessCode.set(value);
    setValue("");
    setSaved(true);
    setMessage("Access code saved on this device.");
  }

  function remove() {
    accessCode.clear();
    setSaved(false);
    setMessage("Access code removed from this device.");
  }

  return (
    <div className="animate-fade-up max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted">Keep things simple.</p>
      </div>

      <section>
        <h2 className="text-lg font-semibold tracking-tight">Access</h2>
        <Card className="mt-4 p-5">
          <p className="text-sm">
            {saved ? "An access code is saved on this device." : "No access code is saved on this device."}
          </p>
          <p className="mt-1 text-sm text-muted">
            If this product asks for an access code, enter it once and it will be remembered here.
          </p>
          <form className="mt-4 flex flex-col gap-2 sm:flex-row" onSubmit={save}>
            <input
              type="password"
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={saved ? "Enter a new access code" : "Access code"}
              autoComplete="off"
              className="w-full rounded-lg border border-line px-3 py-2.5 text-sm outline-none focus:border-accent sm:max-w-xs"
            />
            <Button type="submit" disabled={!value.trim()}>
              {saved ? "Replace" : "Save"}
            </Button>
            {saved && (
              <Button type="button" variant="secondary" onClick={remove}>
                Remove
              </Button>
            )}
          </form>
          {message && <p className="mt-3 text-sm text-good">{message}</p>}
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-semibold tracking-tight">About</h2>
        <Card className="mt-4 space-y-3 p-5 text-[15px] leading-relaxed">
          <p>
            Startup Validator helps founders test an idea against real evidence before building it. It
            researches the market, finds competitors, and checks every claim against its source.
          </p>
          <p>
            The verdict follows fixed rules, not opinion. When the evidence is weak, the report says so
            instead of guessing.
          </p>
          <p className="text-sm text-muted">
            This is decision support, not a prediction of success.
          </p>
        </Card>
      </section>
    </div>
  );
}