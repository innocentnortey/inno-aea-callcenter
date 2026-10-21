import type { ApiError } from "@/api/errors";
import type { Role } from "@/lib/roles";
import { ErrorLine } from "@/components/shared/states";
import { RoleNotAllowedPanel } from "@/components/shell/RoleGate";
import { readErrorText } from "./format";

export function ReadError(props: { error: ApiError; role: Role | null; allow?: Role[]; didntLoad: string; onRetry(): void }) {
  const { error, role, allow, didntLoad, onRetry } = props;
  if (error.isRoleNotAllowed && allow && role) {
    return <RoleNotAllowedPanel role={role} allow={allow} reset={error.details?.reason === "role_reset"} />;
  }
  return <ErrorLine message={readErrorText(error, didntLoad)} onRetry={onRetry} />;
}
