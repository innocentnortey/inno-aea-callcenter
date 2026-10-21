// The ONLY file in the app that calls fetch. The dev layer swaps the transport through setTransport().
import { SseParser } from "./sse";
import { emitAuthLost, emitRoleDenied } from "./refetch";
import type { OperationId } from "./client";

export interface CallContext { op: OperationId; method: string; path: string; body?: unknown }
export type StreamStatus = "connecting" | "open" | "reconnecting" | "closed";
export interface StreamSpec {
  op: "streamChatEvents" | "streamCaseEvents";
  path: Record<string, string>; // { thread_id } or { reference }
  lastEventId?: number;
  onEvent(data: unknown, id: number | null, eventType: string): void;
  onStatus(status: StreamStatus): void;
}
export interface StreamHandle { close(): void }
export interface ApiTransport {
  fetch(ctx: CallContext, url: string, init: RequestInit): Promise<Response>;
  openStream(spec: StreamSpec): StreamHandle;
}

const STREAM_PATH: Record<StreamSpec["op"], (p: Record<string, string>) => string> = {
  streamChatEvents: (p) => `/api/chat/sessions/${encodeURIComponent(p.thread_id ?? "")}/events`,
  streamCaseEvents: (p) => `/api/staff/cases/${encodeURIComponent(p.reference ?? "")}/events`,
};
const BACKOFF_MS = [1000, 2000, 4000, 5000];
const STOP_STATUSES = new Set([401, 403, 404, 410]);

/** A 401 on a stream is the same "signed out / expired" signal every other call raises; 403 asks the session to be read again; 404/410 stop silently. */
async function reportAuthLost(res: Response): Promise<void> {
  let reason: "none" | "expired" = "none";
  try {
    const body = (await res.json()) as { error?: { details?: { reason?: unknown } } };
    if (body?.error?.details?.reason === "expired") reason = "expired";
  } catch {
    /* no readable body: plain "none" */
  }
  emitAuthLost(reason);
}

function openStream(spec: StreamSpec): StreamHandle {
  const ctrl = new AbortController();
  let lastId = spec.lastEventId ?? null;
  let closed = false;
  const url = STREAM_PATH[spec.op](spec.path);
  // After close() nothing reaches the caller: no frames, no status (a closed handle is stale).
  const status = (st: StreamStatus) => { if (!closed) spec.onStatus(st); };

  async function run() {
    let attempt = 0;
    status("connecting");
    while (!closed) {
      try {
        const headers: Record<string, string> = { Accept: "text/event-stream" };
        if (lastId !== null) headers["Last-Event-ID"] = String(lastId);
        const res = await fetch(url, { headers, credentials: "include", signal: ctrl.signal });
        if (STOP_STATUSES.has(res.status)) {
          if (res.status === 401 && !closed) await reportAuthLost(res);
          if (res.status === 403 && !closed) emitRoleDenied(); // the role changed on the server: the session is read again
          break;
        }
        if (!res.ok || !res.body) throw new Error(`stream status ${res.status}`);
        status("open");
        attempt = 0;
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        const parser = new SseParser();
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          for (const frame of parser.push(dec.decode(value, { stream: true }))) {
            if (frame.id !== null && (lastId === null || frame.id > lastId)) lastId = frame.id;
            if (!frame.data) continue; // heartbeat comment
            if (closed) return;
            try {
              spec.onEvent(JSON.parse(frame.data), frame.id, frame.event);
            } catch {
              /* a malformed frame is skipped */
            }
          }
        }
      } catch {
        if (closed) break;
      }
      if (closed) break;
      status("reconnecting");
      const wait = BACKOFF_MS[Math.min(attempt++, BACKOFF_MS.length - 1)];
      await new Promise((r) => setTimeout(r, wait));
    }
    status("closed");
  }
  void run();
  return { close() { closed = true; ctrl.abort(); } };
}

export const defaultTransport: ApiTransport = {
  fetch: (_ctx, url, init) => fetch(url, { ...init, credentials: "include" }),
  openStream,
};

let current: ApiTransport = defaultTransport;
export function setTransport(t: ApiTransport): void { current = t; }
export function getTransport(): ApiTransport { return current; }
