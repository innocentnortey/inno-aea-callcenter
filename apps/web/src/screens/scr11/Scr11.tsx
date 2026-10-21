import type { components } from "@/api/types.gen";
import { useOp } from "@/api/useOp";
import { EmptyState, StaleLine } from "@/components/shared/states";
import { Time } from "@/components/shared/Time";
import { AppFrame } from "@/components/shell/AppFrame";
import { DemoPageHeader, Main } from "@/components/shell/chrome";
import { Card, CardBody, CardHeader, CardRow, Skeleton } from "@/components/ui";
import { useSession } from "@/state/session";
import { dateOnlyToIso, formatShare, nOfN } from "../reads/format";
import { ReadError } from "../reads/ReadError";
import { ScreenTitle } from "../reads/ScreenTitle";
import { EvalMeasuresTable } from "./EvalMeasuresTable";
import { buildEvalRows, formatRange, hasTargets, mixSummary } from "./evalRows";

type EvalRun = components["schemas"]["EvalRun"];

export default function Scr11() {
  return (
    <AppFrame variant="page">
      <DemoPageHeader title="Evaluation" subtitle="Latest run" />
      <Main className="flex flex-col gap-4 p-4">
        <ScreenTitle id="SCR-11">Evaluation report</ScreenTitle>
        <Report />
      </Main>
    </AppFrame>
  );
}

function MixTable({ run, caption }: { run: EvalRun; caption: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-ui">
        <caption className="px-3 py-2 text-left text-small text-text-muted">{caption}</caption>
        <thead>
          <tr className="text-left text-small text-text-muted">
            {["Category", "Cases", "Origin", "What it tests"].map((h) => <th key={h} scope="col" className="px-3 py-2 font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {run.mix.map((m, i) => (
            <tr key={`${i}-${m.category}`} className="border-t border-dashed border-border-hair">
              <th scope="row" className="px-3 py-2 text-left font-semibold">{m.category}</th>
              <td className="px-3 py-2">{m.count}</td>
              <td className="px-3 py-2">{m.origin === "transcript" ? "Transcript" : "Synthetic"}</td>
              <td className="px-3 py-2">{m.tests ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Report() {
  const { role } = useSession();
  const res = useOp("getLatestEval", {});
  const d = res.data;
  if (d === undefined && res.error) {
    return <ReadError error={res.error} role={role} didntLoad="The evaluation report didn't load. Try again." onRetry={() => void res.refetch()} />;
  }
  if (d === undefined) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton height={96} />
        <Skeleton height={32} rows={6} />
      </div>
    );
  }
  const ho = d.splits.held_out;
  const dv = d.splits.dev;
  if (!ho && !dv) {
    return <EmptyState title="No evaluation run yet." body="When one runs, its results appear here with their test set. No number is shown before then." />;
  }
  const rows = buildEvalRows(d.splits);
  const forVersion = (ho ?? dv)!;
  const stale = forVersion.agent_version !== d.current_agent_version;
  const runLine = (run: EvalRun) => (
    <>{run.run_id} {"·"} <Time iso={dateOnlyToIso(run.date)} format="day" /> {"·"} {run.size} cases</>
  );
  return (
    <div className="flex flex-col gap-4">
      {stale ? (
        <StaleLine>{`This run used an earlier version of the agent (${forVersion.agent_version}); the deployed version is ${d.current_agent_version}.`}</StaleLine>
      ) : null}
      <Card aria-label="Headline">
        <CardHeader as="h2" title="Headline" />
        <CardBody className="flex flex-col gap-1">
          {d.headline && ho ? (
            <>
              <p className="text-small text-text-muted">{d.headline.label}</p>
              <p className="t-time-hero">{formatShare(d.headline.value)}</p>
              <p className="text-ui">{nOfN(d.headline.numerator, d.headline.denominator, "held-out cases")}</p>
              {formatRange(d.headline) ? <p className="text-small text-text-muted">{formatRange(d.headline)}</p> : null}
              <p className="text-ui">Held-out split: scored only, never tuned against.</p>
              <p className="text-ui"><span className="t-ref">{ho.run_id}</span> {"·"} <Time iso={dateOnlyToIso(ho.date)} format="day" /></p>
            </>
          ) : (
            <>
              <p className="t-lead">No held-out run yet.</p>
              <p className="text-ui text-text-muted">Dev numbers are below, labelled: {d.dev_label}</p>
            </>
          )}
        </CardBody>
      </Card>
      <Card aria-label="Run identity">
        <CardHeader as="h2" title="Run identity" />
        <CardBody>
          {ho ? <CardRow label="Held-out run" hint={mixSummary(ho)}>{runLine(ho)}</CardRow> : null}
          {dv ? <CardRow label="Dev run" hint={mixSummary(dv)}>{runLine(dv)}</CardRow> : null}
        </CardBody>
      </Card>
      <Card aria-label="Measures">
        <CardHeader as="h2" title="Measures" />
        <CardBody>
          <EvalMeasuresTable rows={rows} heldOut={ho} dev={dv} devLabel={d.dev_label} showTarget={hasTargets(rows)} />
        </CardBody>
      </Card>
      <Card aria-label="Test-set mix">
        <CardHeader as="h2" title="Test-set mix" />
        <CardBody className="flex flex-col gap-3">
          {ho ? <MixTable run={ho} caption={`Held-out run ${ho.run_id}`} /> : null}
          {dv ? <MixTable run={dv} caption={`Dev run ${dv.run_id}`} /> : null}
        </CardBody>
      </Card>
      {dv ? (
        <Card aria-label="Dev failures">
          <CardHeader as="h2" title="Dev failures (dev split only, redacted)" />
          <CardBody>
            {dv.dev_failures.length === 0 ? <p className="text-ui">None.</p> : (
              <ul className="flex flex-col gap-1 text-ui">
                {dv.dev_failures.map((f) => (
                  <li key={f.case_id}><span className="t-ref">{f.case_id}</span> {f.redacted_summary}</li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
