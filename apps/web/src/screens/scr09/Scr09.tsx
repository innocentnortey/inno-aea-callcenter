import { useState, type ReactNode } from "react";
import { Link } from "react-router";
import type { components } from "@/api/types.gen";
import { useOp } from "@/api/useOp";
import { EmptyState, StaleLine } from "@/components/shared/states";
import { Time } from "@/components/shared/Time";
import { AppFrame } from "@/components/shell/AppFrame";
import { ConsoleHeader, Main } from "@/components/shell/chrome";
import { RoleGate } from "@/components/shell/RoleGate";
import { Card, CardBody, CardHeader, Skeleton } from "@/components/ui";
import { formatStaffTime, formatTimePoint } from "@/lib/time";
import { caseHref } from "@/routes";
import { useDemoStatus } from "@/state/demoStatus";
import { useSession } from "@/state/session";
import { formatShare, nOfN } from "../reads/format";
import { MeasuresTable } from "../reads/MeasuresTable";
import { MetricTile } from "../reads/MetricTile";
import { ReadError } from "../reads/ReadError";
import { ScreenTitle } from "../reads/ScreenTitle";
import { basisLine, isEmptyOwner, isStale } from "./basis";
import { OpenCases } from "./OpenCases";

type Measure = components["schemas"]["Measure"];
type Open = { key: string; title: string; refs: string[] };
const PANEL = "cases-panel";
const LINK = "link-text";

export default function Scr09() {
  return (
    <AppFrame variant="console">
      <ConsoleHeader />
      <Main className="flex flex-col gap-4 p-4">
        <ScreenTitle id="SCR-9">Business-owner outcomes</ScreenTitle>
        <RoleGate allow={["owner", "supervisor"]}><Outcomes /></RoleGate>
      </Main>
    </AppFrame>
  );
}

function Outcomes() {
  const { role } = useSession();
  const { clock } = useDemoStatus();
  const res = useOp("getOwnerMetrics", {});
  const [open, setOpen] = useState<Open | null>(null);
  const d = res.data;

  if (d === undefined && res.error) {
    return <ReadError error={res.error} role={role} allow={["owner", "supervisor"]} didntLoad="Outcomes didn't load. Try again." onRetry={() => void res.refetch()} />;
  }
  if (d === undefined) {
    return (
      <div className="flex flex-col gap-3">
        {[0, 1, 2].map((i) => <Skeleton key={i} height={120} />)}
        <Skeleton height={32} rows={5} />
      </div>
    );
  }

  const toggle = (key: string, m: Measure) => setOpen((o) => (o?.key === key ? null : { key, title: m.label, refs: m.case_refs }));
  const tile = (key: string, m: Measure, noun: string, extra?: ReactNode, estimate?: boolean) => (
    <MetricTile
      heading={m.label} estimate={estimate} value={formatShare(m.value)} denominatorLine={nOfN(m.numerator, m.denominator, noun)}
      reason={m.value == null ? m.null_reason : null} extra={extra} caseRefs={m.case_refs} denominator={m.denominator}
      open={open?.key === key} onToggle={() => toggle(key, m)} panelId={PANEL}
    />
  );
  const stale = isStale(d.as_of, clock?.now ?? null);

  return (
    <div className="flex flex-col gap-4">
      {stale && clock ? (
        <StaleLine actionLabel="Refresh" onAction={() => void res.refetch()}>
          {`These numbers are as of ${formatTimePoint(d.as_of)}; the demo time is now ${formatStaffTime(clock.now)}.`}
        </StaleLine>
      ) : null}
      {isEmptyOwner(d) ? <EmptyState title="No outcomes yet." body="Numbers appear once conversations end. Nothing here is a target." /> : null}
      <div className="flex flex-col gap-3">
        {tile("in_scope_correct_resolution", d.in_scope_correct_resolution, "in-scope conversations",
          <Link to={d.measured_north_star_link.path} className={`text-ui ${LINK}`}>{d.measured_north_star_link.label}</Link>, true)}
        {tile("promises_kept_on_time", d.promises_kept_on_time, "promises due")}
        {tile("handoffs", d.handoffs, "conversations")}
      </div>
      {open ? <OpenCases key={open.key} id={PANEL} title={`Cases behind "${open.title}"`} refs={open.refs} cases={d.cases} /> : null}
      <p className="text-ui">{basisLine(d)}</p>
      <Card>
        <CardHeader as="h2" title="Outcomes" />
        {d.outcomes.length === 0 ? <CardBody><p className="text-ui text-text-muted">None yet.</p></CardBody> : (
          <MeasuresTable caption="Outcomes of stored conversations" firstColumn="Outcome" rows={d.outcomes} noun="conversations" openKey={open?.key ?? null} onOpen={toggle} panelId={PANEL} keyPrefix="o" />
        )}
      </Card>
      <Card>
        <CardHeader as="h2" title="Handoffs by reason" />
        {d.handoffs_by_reason.length === 0 ? <CardBody><p className="text-ui text-text-muted">None yet.</p></CardBody> : (
          <MeasuresTable caption="Handoffs by reason" firstColumn="Reason" rows={d.handoffs_by_reason} noun="handoffs" openKey={open?.key ?? null} onOpen={toggle} panelId={PANEL} keyPrefix="h" />
        )}
      </Card>
      <Card>
        <CardHeader as="h2" title="Missed promises" />
        <CardBody>
          {d.missed_promises.length === 0 ? <p className="text-ui text-text-muted">None.</p> : (
            <div className="overflow-x-auto">
              <table className="w-full text-ui">
                <caption className="sr-only">Missed promises</caption>
                <thead>
                  <tr className="text-left text-small text-text-muted">
                    <th scope="col" className="px-3 py-2 font-semibold">Case</th>
                    <th scope="col" className="px-3 py-2 font-semibold">Due</th>
                    <th scope="col" className="px-3 py-2 font-semibold">Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {d.missed_promises.map((m) => (
                    <tr key={m.reference} className="border-t border-dashed border-border-hair">
                      <th scope="row" className="px-3 py-2 text-left"><Link to={caseHref(m.reference)} className={`t-ref ${LINK}`}>{m.reference}</Link></th>
                      <td className="px-3 py-2"><Time iso={m.due_at} format="short" /></td>
                      <td className="px-3 py-2">{m.outcome}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>
      <p className="text-ui">
        System health is on the <Link to="/monitoring" className={LINK}>Monitoring</Link> page. Evaluation results are on the <Link to="/eval" className={LINK}>Evaluation</Link> page.
      </p>
    </div>
  );
}
