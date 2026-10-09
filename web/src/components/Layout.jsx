import { NavLink, Outlet } from "react-router-dom";
import { Brain, Compass, History, Plus, Settings } from "lucide-react";

const MAIN = [
  { to: "/", label: "Validate Idea", icon: Plus, end: true },
  { to: "/validations", label: "Past Validations", icon: History },
  { to: "/memory", label: "Founder Memory", icon: Brain },
];
const SETTINGS = { to: "/settings", label: "Settings", icon: Settings };

const sideClass = ({ isActive }) =>
  `flex items-center justify-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors lg:justify-start ${
    isActive ? "bg-accent-soft text-accent" : "text-muted hover:bg-stone-100 hover:text-ink"
  }`;

const bottomClass = ({ isActive }) =>
  `flex flex-col items-center gap-1 py-2 text-[11px] font-medium ${
    isActive ? "text-accent" : "text-muted"
  }`;

export default function Layout() {
  const SettingsIcon = SETTINGS.icon;

  return (
    <div className="min-h-screen">
      {/* tablet and desktop: fixed sidebar (icons only on tablet) */}
      <aside className="fixed inset-y-0 left-0 z-20 hidden flex-col border-r border-line bg-white md:flex md:w-16 lg:w-60">
        <div className="flex h-16 items-center justify-center gap-2 lg:justify-start lg:px-5">
          <Compass className="h-6 w-6 text-accent" />
          <span className="hidden text-[15px] font-semibold tracking-tight lg:inline">
            Startup Validator
          </span>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-2 py-2 lg:px-3">
          {MAIN.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={sideClass} title={label}>
              <Icon className="h-4.5 w-4.5 shrink-0" />
              <span className="hidden lg:inline">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-line px-2 py-3 lg:px-3">
          <NavLink to={SETTINGS.to} className={sideClass} title={SETTINGS.label}>
            <SettingsIcon className="h-4.5 w-4.5 shrink-0" />
            <span className="hidden lg:inline">{SETTINGS.label}</span>
          </NavLink>
        </div>
      </aside>

      <main className="md:pl-16 lg:pl-60">
        <div className="mx-auto max-w-275 px-5 py-8 pb-28 md:px-8 md:py-12 md:pb-12">
          <Outlet />
        </div>
      </main>

      {/* phone: bottom navigation */}
      <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-4 border-t border-line bg-white md:hidden">
        {[...MAIN, SETTINGS].map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={bottomClass}>
            <Icon className="h-5 w-5" />
            {label.split(" ")[0]}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}