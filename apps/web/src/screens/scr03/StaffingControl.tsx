import { ErrorLine, ResultLine, StaleLine } from "@/components/shared/states";
import { Card, CardBody, CardHeader, CardRow } from "@/components/ui";
import { Switch } from "./Switch";
import type { useStaffingControl } from "./useStaffingControl";
import { CHECKING, READ_ERROR, STALE, SWITCH_HINT, SWITCH_LABEL, WRITE_ERROR, staffingSuccessLine } from "./copy";

export function StaffingControl({ api }: { api: ReturnType<typeof useStaffingControl> }) {
  const r = api.result;
  return (
    <Card>
      <CardHeader as="h2" title="Staffing" />
      <CardBody>
        <CardRow label="Staffing">{api.label ?? CHECKING}</CardRow>
        {api.phase === "error" ? <ErrorLine className="mt-2" message={READ_ERROR} onRetry={() => void api.refetch()} /> : null}
        <div className="mt-2">
          <Switch checked={api.checked} disabled={api.disabled} onCheckedChange={(v) => void api.toggle(v)} label={SWITCH_LABEL} hint={SWITCH_HINT} />
        </div>
        <div className="mt-2" aria-live="polite">
          {r?.kind === "success" ? <ResultLine>{staffingSuccessLine(r.mode, r.converted)}</ResultLine> : null}
          {r?.kind === "error" ? <ResultLine>{WRITE_ERROR}</ResultLine> : null}
          {r?.kind === "stale" ? <StaleLine>{STALE}</StaleLine> : null}
        </div>
      </CardBody>
    </Card>
  );
}
