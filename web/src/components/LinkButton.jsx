import { Link } from "react-router-dom";

export function LinkButton({ to, variant = "primary", className = "", children }) {
  const styles =
    variant === "primary"
      ? "bg-accent text-white hover:bg-indigo-700"
      : "border border-line bg-white text-ink hover:bg-stone-50";
  return (
    <Link
      to={to}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${styles} ${className}`}
    >
      {children}
    </Link>
  );
}