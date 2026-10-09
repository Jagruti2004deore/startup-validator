import { Card } from "./ui";

export function EmptyState({ icon: Icon, title, text, action }) {
  return (
    <Card className="animate-fade-up px-6 py-14 text-center">
      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-accent-soft">
        <Icon className="h-5 w-5 text-accent" />
      </div>
      <h2 className="mt-4 text-lg font-semibold tracking-tight">{title}</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-muted">{text}</p>
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </Card>
  );
}