import { AlertCircle } from "lucide-react";

export function Card({ children, className = "" }) {
  return (
    <div className={`rounded-2xl border border-line bg-white shadow-card ${className}`}>
      {children}
    </div>
  );
}

export function Button({ variant = "primary", className = "", ...props }) {
  const styles =
    variant === "primary"
      ? "bg-accent text-white hover:bg-indigo-700 disabled:bg-stone-300"
      : "border border-line bg-white text-ink hover:bg-stone-50 disabled:text-stone-400";
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed ${styles} ${className}`}
    />
  );
}

export function Notice({ title, children, action }) {
  return (
    <div className="animate-fade-up rounded-2xl border border-line bg-white p-5 shadow-card">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-caution" />
        <div className="min-w-0">
          <p className="font-medium">{title}</p>
          <p className="mt-1 text-sm text-muted">{children}</p>
          {action && <div className="mt-4">{action}</div>}
        </div>
      </div>
    </div>
  );
}