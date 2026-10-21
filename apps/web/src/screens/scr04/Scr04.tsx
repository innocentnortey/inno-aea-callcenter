import { useEffect } from "react";
import { Link } from "react-router";
import { useOp } from "@/api/useOp";
import { AppFrame } from "@/components/shell/AppFrame";
import { DemoPageHeader, Main } from "@/components/shell/chrome";
import { ErrorLine } from "@/components/shared/states";
import { ROLES, ROLE_LABEL } from "@/lib/roles";
import { screenById } from "@/routes";
import { useSession } from "@/state/session";
import { RoleChoices, type RoleChoice } from "./RoleChoices";
import { BACK, H1, STATEMENT } from "./copy";

export default function Scr04() {
  const { role, switching, switchError, switchRole } = useSession();
  const { data } = useOp("listDemoRoles", {});
  useEffect(() => { document.title = "SCR-4 · Role switch · Meridian"; }, []);

  // If the list fails (or is still loading), fall back to the fixed labels with no description line.
  const choices: RoleChoice[] = data
    ? data.roles.map((r) => ({ role: r.role, title: r.display_name, line: r.sees }))
    : ROLES.map((r) => ({ role: r, title: ROLE_LABEL[r].full, line: null }));

  return (
    <AppFrame variant="page">
      <DemoPageHeader title="Role switch" showDemoBar />
      <Main className="p-4">
        <h1 className="t-title">{H1}</h1>
        <p className="mt-2 text-body">{STATEMENT}</p>
        <RoleChoices roles={choices} current={role} switching={switching} onPick={(r) => void switchRole(r)} />
        {switchError ? <ErrorLine className="mt-3" message={switchError} /> : null}
        <p className="mt-6"><Link to={screenById("SCR-3").path} className="link-text">{BACK}</Link></p>
      </Main>
    </AppFrame>
  );
}
