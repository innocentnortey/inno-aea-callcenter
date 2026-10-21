import { type ReactNode } from "react";
import { ROLE_LABEL, type Role } from "@/lib/roles";
import { useSession } from "@/state/session";
import { RoleSwitch } from "./RoleSwitch";

export function RoleNotAllowedPanel({ role, allow, reset }: { role: Role; allow: Role[]; reset?: boolean }) {
  let text: string;
  if (reset) text = "The demo was reset, so you're back to the customer role. Pick a role again.";
  else if (role === "customer") text = "You're acting as the customer. Switch to a staff role to see this.";
  else text = `You're acting as ${ROLE_LABEL[role].full}. Switch to ${allow.map((r) => ROLE_LABEL[r].full).join(" or ")} to see this.`;
  return (
    <div className="flex flex-col gap-3 p-4">
      <p className="text-body">{text}</p>
      <RoleSwitch />
    </div>
  );
}

/** Renders children only when the current role is allowed; otherwise the panel and nothing else. */
export function RoleGate({ allow, children }: { allow: Role[]; children: ReactNode }) {
  const { role } = useSession();
  if (!role) return null;
  if (!allow.includes(role)) return <RoleNotAllowedPanel role={role} allow={allow} />;
  return <>{children}</>;
}
