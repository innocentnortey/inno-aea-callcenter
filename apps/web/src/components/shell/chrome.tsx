import { type ReactNode } from "react";
import { NavLink } from "react-router";
import { cn } from "@/lib/cx";
import { CONSOLE_NAV, ROLE_LABEL } from "@/lib/roles";
import { formatClockLabel, formatDemoDate } from "@/lib/time";
import { Button } from "@/components/ui/Button";
import { IconInfo, IconSignOut } from "@/components/ui/icons";
import { PersonDisc } from "@/components/shared/marks";
import { useDemoStatus } from "@/state/demoStatus";
import { useSession } from "@/state/session";
import { RoleSwitch } from "./RoleSwitch";

export function SignOutButton() {
  const { signOut } = useSession();
  return (
    <Button variant="text" icon={<IconSignOut size={16} strokeWidth={1.8} aria-hidden="true" />} onClick={() => void signOut()}>
      Sign out
    </Button>
  );
}

/** "Fri Oct 16, 2026 (demo date) · Nobody online" in a 12 px centred grey strip. No icon. */
export function DemoBar({ className }: { className?: string }) {
  const { clock, staffing } = useDemoStatus();
  return (
    <div className={cn("bg-[var(--demo-bar-bg)] px-4 py-1 text-center text-caption text-[color:var(--demo-bar-text)]", className)}>
      {clock ? formatDemoDate(clock.now) : "Demo date loading"}
      {" · "}
      {staffing ? staffing.label : "Staffing loading"}
    </div>
  );
}

export function StaffingBanner({ className }: { className?: string }) {
  const { staffing } = useDemoStatus();
  if (staffing?.mode !== "simulated_on_shift") return null;
  return (
    <div className={cn("flex items-center gap-2 bg-[var(--banner-bg)] px-4 py-2 text-small", className)}>
      <IconInfo size={16} strokeWidth={1.8} aria-hidden="true" />
      <p>{staffing.banner ?? "Simulated staffing (demo). No Meridian employee is online."}</p>
    </div>
  );
}

export function ConsoleHeader() {
  const { session, role } = useSession();
  const { clock, staffing } = useDemoStatus();
  const nav = role && role !== "customer" ? CONSOLE_NAV[role] : [];
  const name = session?.display_name ?? (role ? ROLE_LABEL[role].full : "");
  return (
    <header className="border-b border-border-hair bg-surface">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2">
        <p className="t-name">Meridian {"·"} Staff console</p>
        <p className="flex items-center gap-2 text-ui">
          <PersonDisc initial={name || "?"} size={32} />
          <span>{name}</span>
        </p>
        <p className="text-caption text-text-muted">
          {clock ? formatClockLabel(clock.now) : ""}
          {staffing ? ` · ${staffing.label}` : ""}
          {clock ? <span className="sr-only"> {formatDemoDate(clock.now)}</span> : null}
        </p>
        <nav aria-label="Staff" className="flex items-center gap-3">
          {nav.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => cn("text-ui", isActive ? "border-b-2 border-[color:var(--tab-underline)] font-semibold" : "text-text-muted")}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto"><SignOutButton /></div>
      </div>
      <div className="px-4 pb-2"><RoleSwitch density="console" /></div>
      <StaffingBanner />
    </header>
  );
}

export function DemoPageHeader({ title, subtitle, showDemoBar = true }: { title: string; subtitle?: string; showDemoBar?: boolean }) {
  return (
    <header className="border-b border-border-hair bg-surface">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="min-w-0 flex-1">
          <p className="t-name">Meridian Home Comfort</p>
          <p className="text-small text-text-muted">{title}{subtitle ? ` · ${subtitle}` : ""}</p>
        </div>
        <NavLink to="/" end className="link-text inline-flex min-h-11 items-center text-small">Back to chat</NavLink>
        <SignOutButton />
      </div>
      <div className="px-4 pb-3"><RoleSwitch /></div>
      {showDemoBar ? <DemoBar /> : null}
    </header>
  );
}

export function Main({ children, id = "main", className }: { children: ReactNode; id?: "main"; className?: string }) {
  return <main id={id} tabIndex={-1} className={cn("outline-none", className)}>{children}</main>;
}
