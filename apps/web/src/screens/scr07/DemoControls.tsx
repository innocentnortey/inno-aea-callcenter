import { useState } from "react";
import { useAction } from "@/api/useOp";
import { ResultLine } from "@/components/shared/states";
import { Button, Disclosure, Tag } from "@/components/ui";
import { formatClockLabel } from "@/lib/time";
import { useDemoStatus } from "@/state/demoStatus";
import { ADVANCE_STEPS, CLOCK_ERROR, NO_BACK, STAFFING_ERROR, advanceLine, shiftLine } from "./copy";

export interface DemoControlsProps { demoNow: string | null; onChanged(): Promise<void> }
type Mode = "nobody_online" | "simulated_on_shift";

export function DemoControls({ demoNow, onChanged }: DemoControlsProps) {
  const { staffing, clock, refresh } = useDemoStatus();
  const advance = useAction("advanceDemoClock");
  const shift = useAction("setStaffing");
  const [pendingMode, setPendingMode] = useState<Mode | null>(null);
  const [result, setResult] = useState("");
  const [desktop] = useState(() => window.matchMedia("(min-width: 700px)").matches);
  const saving = advance.pending || shift.pending;
  const t = demoNow ?? clock?.now ?? null;
  const checked = pendingMode ? pendingMode === "simulated_on_shift" : staffing?.mode === "simulated_on_shift";

  async function onShift(next: boolean) {
    const mode: Mode = next ? "simulated_on_shift" : "nobody_online";
    setResult("");
    setPendingMode(mode);
    try {
      const res = await shift.run({ body: { mode } });
      setResult(shiftLine(res.mode === "simulated_on_shift", res.converted_cases));
      await refresh();
      await onChanged();
    } catch {
      setResult(STAFFING_ERROR);
      await refresh();
    } finally {
      setPendingMode(null);
    }
  }
  async function onAdvance(step: (typeof ADVANCE_STEPS)[number]["step"]) {
    setResult("");
    try {
      const res = await advance.run({ body: { step } });
      setResult(advanceLine(res.now, res.became_overdue));
      await refresh();
      await onChanged();
    } catch {
      setResult(CLOCK_ERROR);
    }
  }

  return (
    <section aria-label="Demo controls" className="rounded-card border border-border-hair bg-surface-well px-3">
      <Disclosure
        open={desktop}
        summary={
          <span className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">Demo controls</span>
            <Tag>Demo</Tag>
            {t ? <span className="text-small text-text-muted">{formatClockLabel(t)}</span> : null}
          </span>
        }
      >
        <div className="flex flex-col gap-3 pb-3">
          <p className="text-ui">
            Demo time: {t ? <time dateTime={t}>{formatClockLabel(t)}</time> : "Loading…"}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <label className="inline-flex min-h-[var(--control-h-console)] items-center gap-2 text-ui">
              <input
                type="checkbox" role="switch" aria-checked={Boolean(checked)} checked={Boolean(checked)}
                disabled={saving || staffing === null} onChange={(e) => void onShift(e.target.checked)}
                className="size-4 accent-[var(--color-accent)]"
              />
              <span>Simulated shift: {checked ? "on" : "off"}</span>
            </label>
            {staffing === null ? <span className="text-small text-text-muted">Checking{"…"}</span> : null}
          </div>
          <div className="flex flex-col gap-1">
            <p className="text-small font-semibold">Advance simulated time</p>
            <div className="flex flex-wrap gap-2">
              {ADVANCE_STEPS.map((s) => (
                <Button key={s.step} density="console" disabled={saving} onClick={() => void onAdvance(s.step)}>{s.label}</Button>
              ))}
            </div>
            <p className="text-small text-text-muted">{NO_BACK}</p>
          </div>
          {result ? <ResultLine id="demo-controls-result">{result}</ResultLine> : null}
        </div>
      </Disclosure>
    </section>
  );
}
