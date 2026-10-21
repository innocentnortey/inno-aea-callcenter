import { useEffect } from "react";
import { AppFrame } from "@/components/shell/AppFrame";
import { DemoPageHeader, Main } from "@/components/shell/chrome";
import { DemoLinks } from "./DemoLinks";
import { RealVsSimulated } from "./RealVsSimulated";
import { ResetControl } from "./ResetControl";
import { StaffingControl } from "./StaffingControl";
import { TwoRoles } from "./TwoRoles";
import { useResetDemo } from "./useResetDemo";
import { useStaffingControl } from "./useStaffingControl";
import { H1 } from "./copy";

export default function Scr03() {
  const staffing = useStaffingControl();
  const reset = useResetDemo();
  useEffect(() => { document.title = "SCR-3 · Demo guide and controls · Meridian"; }, []);
  return (
    <AppFrame variant="page">
      <DemoPageHeader title="Demo guide" showDemoBar />
      <Main className="flex flex-col gap-4 p-4">
        <h1 className="t-title">{H1}</h1>
        <RealVsSimulated />
        <StaffingControl api={staffing} />
        <TwoRoles />
        <DemoLinks />
        <ResetControl api={reset} />
      </Main>
    </AppFrame>
  );
}
