import { useState, useSyncExternalStore } from "react";
import { OPS, type OperationId, type Role } from "@/api/client";
import { defaultTransport } from "@/api/transport";
import { refetchAll } from "@/api/refetch";
import { ROLES } from "@/lib/roles";
import { SCREENS, screenById, type ScreenId } from "@/routes";
import { setTheme } from "@/state/theme";
import { applyScenario, syncUrl } from "./apply";
import { calls, clearCalls, countsByOp, subscribeCalls } from "./calllog";
import { chatEvents } from "./stream/events";
import { getPathname, navigateTo, subscribeLocation } from "./nav";
import { MATRIX, STANDARD_STATES } from "./scenarios/matrix";
import { scenariosFor, screenForPath, sharedScenarios } from "./scenarios";
import { applyRole, clearSessionCookie, fakeLoginRules } from "./session-fake";
import { dropStreams, emitToStream, openStreamKeys, resumeStreams, subscribeStreams } from "./stream/dev-stream";
import { getWorld, resetWorld, setWorld, subscribe } from "./world";

type Tab = "States" | "Session" | "Calls" | "Stream" | "Look";
const TABS: Tab[] = ["States", "Session", "Calls", "Stream", "Look"];
const CASE_REF = "MHC-C-0007"; // OpenAPI example reference

const btn = "rounded-control border border-[color:var(--btn-send-text)] px-2 py-1 text-small text-[color:var(--btn-send-text)] hover:underline disabled:opacity-60";
const sel = "rounded-control bg-surface text-text border border-border-control px-1 py-1 text-small";

function useWorld() { return useSyncExternalStore(subscribe, getWorld); }
function usePath() { return useSyncExternalStore(subscribeLocation, getPathname); }

function StatesTab() {
  const path = usePath();
  const world = useWorld();
  useSyncExternalStore(subscribeCalls, calls);
  const screen = screenForPath(path);
  const [jump, setJump] = useState<ScreenId>("SCR-1");
  const scenarios = screen ? scenariosFor(screen) : [];
  const flow = scenarios.filter((s) => s.flowState);
  const usedOps = [...new Set(calls().map((c) => c.op))] as OperationId[];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-small">Jump to
          <select className={`${sel} ml-1`} value={jump} onChange={(e) => setJump(e.target.value as ScreenId)}>
            {SCREENS.map((s) => <option key={s.id} value={s.id}>{s.id} {s.title}</option>)}
          </select>
        </label>
        <button className={btn} onClick={() => { const d = screenById(jump); navigateTo(d.path.replace(":reference", CASE_REF) + window.location.search); refetchAll(); }}>Go</button>
        <button className={btn} onClick={() => { setWorld({ forces: {}, scenarioId: null }); syncUrl(); refetchAll(); }}>Clear forces</button>
        <span className="text-caption">On {screen ?? "no screen"}{world.scenarioId ? ` · scenario ${world.scenarioId}` : ""}</span>
      </div>
      {screen ? (
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 min-[900px]:grid-cols-4">
          {STANDARD_STATES.map((st) => {
            const cell = MATRIX[screen][st];
            const list = scenarios.filter((s) => s.state === st);
            return (
              <div key={st}>
                <p className="text-small font-semibold">{st}</p>
                {!cell.real ? <p className="text-caption opacity-70">{cell.reason}</p> : list.length === 0 ? <p className="text-caption opacity-70">no scenario yet</p> : null}
                {list.map((s) => <button key={s.id} className={`${btn} mb-1 block text-left`} onClick={() => void applyScenario(s.id)}>{s.label}</button>)}
              </div>
            );
          })}
        </div>
      ) : null}
      {flow.length ? <p className="text-caption">Flow states: {flow.map((s) => s.flowState).join(" · ")}</p> : null}
      <div>
        <p className="text-small font-semibold">Anywhere</p>
        <div className="flex flex-wrap gap-1">
          {sharedScenarios().map((s) => <button key={s.id} className={btn} onClick={() => void applyScenario(s.id)}>{s.label}</button>)}
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {usedOps.map((op) => {
          const forced = world.forces[op];
          const names = [...new Set(OPS[op].responses.flatMap((r) => r.examples))];
          return (
            <label key={op} className="text-caption">{op}
              <select
                className={`${sel} ml-1`}
                value={forced && "example" in forced ? forced.example : ""}
                onChange={(e) => {
                  const forces = { ...getWorld().forces };
                  if (e.target.value) {
                    const status = OPS[op].responses.find((r) => r.examples.includes(e.target.value))?.status;
                    forces[op] = { example: e.target.value, status };
                  } else delete forces[op];
                  setWorld({ forces });
                  syncUrl();
                  refetchAll();
                }}
              >
                <option value="">default</option>
                {names.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          );
        })}
      </div>
    </div>
  );
}

function SessionTab() {
  const w = useWorld();
  return (
    <div className="flex flex-wrap items-center gap-2">
      <label className="text-small"><input type="checkbox" checked={w.signedIn} onChange={(e) => { setWorld({ signedIn: e.target.checked }); syncUrl(); refetchAll(); }} /> Fake sign-in</label>
      <label className="text-small">Role
        <select className={`${sel} ml-1`} value={w.role} onChange={(e) => { void applyRole(defaultTransport, e.target.value as Role).then(() => { syncUrl(); refetchAll(); }); }}>
          {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </label>
      <button className={btn} onClick={() => fakeLoginRules.expireSession()}>Expire session</button>
      <button className={btn} onClick={() => fakeLoginRules.refuseNext()}>Refuse next login</button>
      <button className={btn} onClick={() => { fakeLoginRules.resetRole(); syncUrl(); refetchAll(); }}>Reset role</button>
      <button className={btn} onClick={() => { resetWorld(); clearSessionCookie(); navigateTo("/login"); }}>Restart</button>
      <button className={btn} onClick={() => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark")}>Toggle theme</button>
      <label className="text-small">Delay
        <select className={`${sel} ml-1`} value={String(w.delayMs)} onChange={(e) => { const v = e.target.value; setWorld({ delayMs: v === "hang" ? "hang" : Number(v) }); syncUrl(); }}>
          <option value="0">off</option><option value="1500">1.5 s</option><option value="4000">4 s</option><option value="hang">hang</option>
        </select>
      </label>
    </div>
  );
}

function CallsTab() {
  const list = useSyncExternalStore(subscribeCalls, calls);
  const counts = countsByOp();
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <button className={btn} onClick={() => void navigator.clipboard?.writeText(JSON.stringify(list, null, 2))}>Copy JSON</button>
        <button className={btn} onClick={clearCalls}>Clear</button>
        <span className="text-caption">{Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(" · ")}</span>
      </div>
      <div className="max-h-48 overflow-auto">
        <table className="w-full text-caption">
          <thead><tr><th className="text-left">Time</th><th className="text-left">Op</th><th className="text-left">Method</th><th className="text-left">Path</th><th className="text-left">Status</th><th className="text-left">Example</th><th className="text-left">ms</th></tr></thead>
          <tbody>
            {[...list].reverse().map((c, i) => (
              <tr key={i}>
                <td>{new Date(c.t).toLocaleTimeString("en-US")}</td><td>{c.op}</td><td>{c.method}</td><td>{c.path}</td>
                <td>{c.status}{c.drift ? <strong> Drift</strong> : null}</td><td>{c.example ?? ""}</td><td>{c.ms}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StreamTab() {
  const open = useSyncExternalStore(subscribeStreams, () => JSON.stringify(openStreamKeys()));
  const keys = JSON.parse(open) as ReturnType<typeof openStreamKeys>;
  return (
    <div className="flex flex-col gap-2">
      <p className="text-caption">{keys.length ? keys.map((k) => `${k.op} ${Object.values(k.path).join("")} (${k.status})`).join(" · ") : "No stream is open. Open a chat or a case first."}</p>
      <div className="flex flex-wrap gap-1">
        {(Object.keys(chatEvents) as (keyof typeof chatEvents)[]).map((name) => (
          <button key={name} className={btn} disabled={!keys.length} onClick={() => emitToStream("*", chatEvents[name]())}>{name}</button>
        ))}
        <button className={btn} disabled={!keys.length} onClick={dropStreams}>Drop connection</button>
        <button className={btn} disabled={!keys.length} onClick={resumeStreams}>Reconnect</button>
      </div>
    </div>
  );
}

export function Panel() {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState<Tab>("States");
  if (!expanded) {
    return (
      <button
        className="fixed right-2 top-2 z-50 min-[700px]:bottom-2 min-[700px]:top-auto rounded-control bg-[var(--btn-send-bg)] px-3 py-1 text-small font-semibold text-[color:var(--btn-send-text)]"
        onClick={() => setExpanded(true)}
      >
        Prototype only
      </button>
    );
  }
  return (
    <section aria-label="Prototype controls" className="fixed inset-x-0 bottom-0 z-50 max-h-[55vh] overflow-auto bg-[var(--btn-send-bg)] p-3 text-[color:var(--btn-send-text)]">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <strong className="text-small">Prototype only</strong>
        {TABS.map((t) => (
          <button key={t} className={`${btn} ${tab === t ? "underline" : ""}`} aria-pressed={tab === t} onClick={() => setTab(t)}>{t}</button>
        ))}
        <button className={`${btn} ml-auto`} onClick={() => setExpanded(false)}>Collapse</button>
      </div>
      {tab === "States" ? <StatesTab /> : null}
      {tab === "Session" ? <SessionTab /> : null}
      {tab === "Calls" ? <CallsTab /> : null}
      {tab === "Stream" ? <StreamTab /> : null}
      {tab === "Look" ? <p className="text-small"><a className="underline" href="/__kit?signedin=1" onClick={(e) => { e.preventDefault(); navigateTo("/__kit?signedin=1"); }}>Open the component kit</a></p> : null}
    </section>
  );
}
