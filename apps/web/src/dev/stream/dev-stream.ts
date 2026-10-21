import type { ApiTransport, StreamHandle, StreamSpec, StreamStatus } from "@/api/transport";
import { SseParser } from "@/api/sse";
import type { StreamScript } from "./types";

interface Open {
  key: string;
  spec: StreamSpec;
  status: StreamStatus;
  nextId: number;
  buffer: { event: unknown }[];
  dropped: boolean;
  timers: ReturnType<typeof setTimeout>[];
  closed: boolean;
}
const open = new Map<string, Open>();
const subs = new Set<() => void>();
let activeScript: StreamScript | null = null;
const notify = () => subs.forEach((cb) => cb());

export function subscribeStreams(cb: () => void): () => void { subs.add(cb); return () => void subs.delete(cb); }
export function openStreamKeys(): { key: string; status: StreamStatus; op: StreamSpec["op"]; path: Record<string, string> }[] {
  return [...open.values()].map((s) => ({ key: s.key, status: s.status, op: s.spec.op, path: s.spec.path }));
}
/** The script a scenario wants played on the next stream that opens (and any already open). */
export function setActiveStreamScript(script: StreamScript | null): void {
  activeScript = script;
  if (script) for (const s of open.values()) if (!s.closed) schedule(s, script);
}

function setStatus(s: Open, status: StreamStatus) { s.status = status; s.spec.onStatus(status); notify(); }
function deliver(s: Open, event: unknown) {
  if (s.closed) return;
  if (s.dropped) { s.buffer.push({ event }); return; }
  const id = s.nextId++;
  const type = (event as { type?: string }).type ?? "message";
  s.spec.onEvent(event, id, type);
  if (type === "demo_reset" || type === "chat_closed") {
    s.closed = true;
    s.timers.forEach(clearTimeout);
    setStatus(s, "closed");
  }
}
function matches(s: Open, script: StreamScript): boolean {
  return !script.thread || Object.values(s.spec.path).includes(script.thread);
}
function schedule(s: Open, script: StreamScript) {
  if (!matches(s, script)) return;
  for (const step of script.steps) s.timers.push(setTimeout(() => deliver(s, step.event), step.afterMs));
  if (script.dropAfterMs !== undefined) s.timers.push(setTimeout(() => drop(s), script.dropAfterMs));
}
function drop(s: Open) { if (!s.closed && !s.dropped) { s.dropped = true; setStatus(s, "reconnecting"); } }
function resume(s: Open) {
  if (s.closed || !s.dropped) return;
  s.dropped = false;
  setStatus(s, "open");
  const pending = s.buffer.splice(0);
  for (const p of pending) deliver(s, p.event); // replay in order, like Last-Event-ID
}

/** Push an event to the streams for `thread` ("*" = every open stream). */
export function emitToStream(thread: string, event: unknown): void {
  for (const s of open.values()) if (thread === "*" || Object.values(s.spec.path).includes(thread)) deliver(s, event);
}
export function dropStreams(): void { open.forEach(drop); }
export function resumeStreams(): void { open.forEach(resume); }

export function createDevStreamOpener(fetchViaDev: ApiTransport["fetch"]): ApiTransport["openStream"] {
  return (spec) => {
    const key = `${spec.op}:${JSON.stringify(spec.path)}`;
    const s: Open = { key, spec, status: "connecting", nextId: (spec.lastEventId ?? 0) + 1, buffer: [], dropped: false, timers: [], closed: false };
    open.set(key, s);
    spec.onStatus("connecting");
    const url = spec.op === "streamChatEvents"
      ? `/api/chat/sessions/${encodeURIComponent(spec.path.thread_id ?? "")}/events`
      : `/api/staff/cases/${encodeURIComponent(spec.path.reference ?? "")}/events`;
    void (async () => {
      try {
        // Prism still validates the cookie, the path and Last-Event-ID; the body is discarded unless the script asks for the frames.
        const res = await fetchViaDev({ op: spec.op, method: "GET", path: url }, url, { method: "GET", headers: { Accept: "text/event-stream" }, credentials: "include" });
        if (s.closed) return;
        if (!res.ok) { s.closed = true; setStatus(s, "closed"); return; }
        const text = await res.text();
        if (s.closed) return;
        setStatus(s, "open");
        if (activeScript?.useFrames) {
          const parser = new SseParser();
          for (const f of parser.push(text)) {
            if (!f.data) continue;
            s.nextId = Math.max(s.nextId, (f.id ?? 0) + 1);
            s.spec.onEvent(JSON.parse(f.data), f.id, f.event);
          }
        }
        if (activeScript) schedule(s, activeScript);
      } catch {
        if (!s.closed) { s.closed = true; setStatus(s, "closed"); }
      }
    })();
    const handle: StreamHandle = {
      close() {
        s.closed = true;
        s.timers.forEach(clearTimeout);
        open.delete(key);
        spec.onStatus("closed");
        notify();
      },
    };
    return handle;
  };
}
