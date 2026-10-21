import { useEffect, useRef } from "react";
import type { components } from "@/api/types.gen";
import { useOp } from "@/api/useOp";
import { StaleLine } from "@/components/shared/states";
import { Time } from "@/components/shared/Time";
import { AppFrame } from "@/components/shell/AppFrame";
import { DemoPageHeader, Main } from "@/components/shell/chrome";
import { Card, CardBody, CardHeader, CardRow, Disclosure, Skeleton, Tag } from "@/components/ui";
import { useAnnounce } from "@/components/ui/LiveRegion";
import { formatTimePoint } from "@/lib/time";
import { useSession } from "@/state/session";
import { formatCount, formatShare, formatTileValue, nOfN } from "../reads/format";
import { ReadError } from "../reads/ReadError";
import { ScreenTitle } from "../reads/ScreenTitle";
import { useNow } from "../reads/useNow";
import { AlertsList } from "./AlertsList";
import { staleLine } from "./dataAge";
import { DEFINITIONS } from "./definitions";
import { SpendBar } from "./SpendBar";

type Tile = components["schemas"]["Tile"];
const DASH = "—";

export default function Scr10() {
  return (
    <AppFrame variant="page">
      <DemoPageHeader title="Monitoring" subtitle="Is it running, and is it right?" />
      <Main className="flex flex-col gap-4 p-4">
        <ScreenTitle id="SCR-10">Monitoring</ScreenTitle>
        <Monitor />
      </Main>
    </AppFrame>
  );
}

function tileHint(t: Tile): string | undefined {
  if (t.value == null) return t.null_reason ?? undefined;
  if (t.numerator != null && t.denominator != null) return `${t.numerator} of ${t.denominator} turns`;
  return undefined;
}

function Monitor() {
  const { role } = useSession();
  const res = useOp("getMonitoring", {}, { pollMs: 30_000 });
  const now = useNow(15_000);
  const announce = useAnnounce();
  const prevFiring = useRef<Set<string> | null>(null);
  const d = res.data;

  useEffect(() => {
    if (!d) return;
    const firing = new Set(d.alerts.filter((a) => a.state === "firing").map((a) => a.type));
    if (prevFiring.current !== null) {
      const fresh = d.alerts.filter((a) => firing.has(a.type) && !prevFiring.current!.has(a.type)).map((a) => a.decision_line);
      if (fresh.length > 0) announce(fresh.join(" "));
    }
    prevFiring.current = firing;
    // announce is stable (memoised in the provider)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d]);

  if (d === undefined && res.error) {
    return <ReadError error={res.error} role={role} didntLoad="Monitoring didn't load. Try again." onRetry={() => void res.refetch()} />;
  }
  if (d === undefined) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton height={20} />
        <Skeleton height={56} rows={6} />
      </div>
    );
  }

  const stale = staleLine(d.as_of, now);
  const empty = d.health.every((t) => t.value === 0 || t.value == null);
  const ce = d.correctness.containment_estimate;
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-ui text-text-muted">{`Updated ${formatTimePoint(d.as_of)} · redacted · traces are not shown here`}</p>
        {stale ? <StaleLine>{stale}</StaleLine> : null}
      </div>
      <AlertsList alerts={d.alerts} />
      {empty ? <p className="text-ui">No conversations since the last reset, so there is nothing to measure yet.</p> : null}
      <Card aria-label="Health">
        <CardHeader as="h2" title="Health" />
        <CardBody>
          {d.health.map((t) => (
            <CardRow key={t.id + t.label} label={t.label} hint={tileHint(t)}>{t.value != null ? formatTileValue(t) : DASH}</CardRow>
          ))}
          <CardRow label="Spend today"><SpendBar todayCents={d.spend.today_cents} capCents={d.spend.cap_cents} /></CardRow>
          <CardRow label="Last health-check restart">
            {d.last_restart ? <Time iso={d.last_restart.at} format="short" /> : "No restart recorded."}
          </CardRow>
          <CardRow label="Trace export">{d.trace_export}</CardRow>
        </CardBody>
      </Card>
      <Card aria-label="Correctness">
        <CardHeader as="h2" title="Correctness" />
        <CardBody>
          <CardRow
            label={<span className="inline-flex flex-wrap items-center gap-2">{ce.label} <Tag>Estimate</Tag></span>}
            hint={ce.value == null ? ce.null_reason ?? undefined : nOfN(ce.numerator, ce.denominator, "live conversations")}
          >
            {formatShare(ce.value)}
          </CardRow>
          <h3 className="t-card-title mt-3">Escalations by reason</h3>
          {d.correctness.escalations_by_reason.length === 0 ? (
            <p className="text-ui">No escalations since the last reset.</p>
          ) : (
            d.correctness.escalations_by_reason.map((t, i) => <CardRow key={`${i}-${t.label}`} label={t.label}>{formatCount(t.value)}</CardRow>)
          )}
        </CardBody>
      </Card>
      <Disclosure summary="What each measure counts">
        <div className="flex flex-col gap-3 pb-2">
          {DEFINITIONS.map((g) => (
            <div key={g.heading}>
              <h3 className="t-card-title">{g.heading}</h3>
              <dl className="text-ui">
                {g.items.map((i) => (
                  <div key={i.term} className="py-1">
                    <dt className="font-semibold">{i.term}</dt>
                    <dd className="text-text-muted">{i.text}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      </Disclosure>
    </div>
  );
}
