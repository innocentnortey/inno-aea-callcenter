import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import type { components } from "@/api/types.gen";
import { useOp } from "@/api/useOp";
import { ResultLine, StaleLine } from "@/components/shared/states";
import { AppFrame } from "@/components/shell/AppFrame";
import { ConsoleHeader, Main } from "@/components/shell/chrome";
import { RoleGate } from "@/components/shell/RoleGate";
import { useDemoStatus } from "@/state/demoStatus";
import { useSession } from "@/state/session";
import { ReadError } from "../reads/ReadError";
import { ScreenTitle } from "../reads/ScreenTitle";
import { AlertList } from "./AlertList";
import { AssignDialog } from "./AssignDialog";
import { EMPTY_ALL, LANES, LOAD_ERROR, liveQueueLine, reviewListLine } from "./copy";
import { DemoControls } from "./DemoControls";
import { Lane } from "./Lane";
import { oversightSignature } from "./signature";

type Row = components["schemas"]["QueueRow"];

export default function Scr07() {
  return (
    <AppFrame variant="console">
      <ConsoleHeader />
      <Main className="flex flex-col gap-4 p-4">
        <ScreenTitle id="SCR-7">Supervisor oversight</ScreenTitle>
        <RoleGate allow={["supervisor"]}><Oversight /></RoleGate>
      </Main>
    </AppFrame>
  );
}

function Oversight() {
  const { role } = useSession();
  const { staffing } = useDemoStatus();
  const res = useOp("getOversight", {}, { pollMs: 10_000, refetchOnFocus: true });
  const quiet = useRef(false);
  const lastSig = useRef<string | null>(null);
  const [updated, setUpdated] = useState(false);
  const [assignLine, setAssignLine] = useState("");
  const [target, setTarget] = useState<Row | null>(null);

  useEffect(() => {
    if (res.data === undefined) return;
    const sig = oversightSignature(res.data);
    if (lastSig.current !== null && sig !== lastSig.current) {
      if (!quiet.current) setUpdated(true);
    } else if (lastSig.current !== null && sig === lastSig.current) {
      setUpdated(false);
    }
    quiet.current = false;
    lastSig.current = sig;
  }, [res.data]);

  async function afterOwnChange() {
    quiet.current = true;
    await res.refetch();
  }

  const d = res.data;
  const allEmpty = d ? LANES.every(({ key }) => d.lanes[key].count === 0) && d.alerts.length === 0 : false;
  let body;
  if (d === undefined && res.error) {
    body = <ReadError error={res.error} role={role} allow={["supervisor"]} didntLoad={LOAD_ERROR} onRetry={() => void res.refetch()} />;
  } else if (d === undefined) {
    body = LANES.map((l) => <Lane key={l.key} title={l.title} loading onAssign={setTarget} />);
  } else {
    body = (
      <>
        {updated ? <StaleLine>Lanes updated.</StaleLine> : null}
        <AlertList alerts={d.alerts} />
        {allEmpty ? <p className="text-ui">{EMPTY_ALL}</p> : null}
        {staffing?.mode === "simulated_on_shift" ? <p className="text-ui">{liveQueueLine(d.live_queue_length)}</p> : null}
        {LANES.map((l) => <Lane key={l.key} title={l.title} lane={d.lanes[l.key]} onAssign={setTarget} />)}
        <p><Link to="/staff/flags" className="text-ui link-text">{reviewListLine(d.new_flags_count)}</Link></p>
        {assignLine ? <ResultLine id="assign-result">{assignLine}</ResultLine> : null}
      </>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      <DemoControls demoNow={d?.demo_now ?? null} onChanged={afterOwnChange} />
      {body}
      <AssignDialog
        row={target}
        onClose={() => setTarget(null)}
        onDone={async (line) => { setAssignLine(line); await afterOwnChange(); }}
      />
    </div>
  );
}

