import type { ApiTransport, CallContext, StreamSpec } from "@/api/transport";

export function jsonResponse(status: number, body?: unknown, headers: Record<string, string> = {}): Response {
  if (status === 204) return new Response(null, { status, headers });
  return new Response(JSON.stringify(body ?? {}), { status, headers: { "Content-Type": "application/json", ...headers } });
}

export function makeFakeTransport(
  handler: (ctx: CallContext, url: string, init: RequestInit) => Response | Promise<Response>,
  onStream?: (spec: StreamSpec) => void,
): ApiTransport {
  return {
    fetch: async (ctx, url, init) => handler(ctx, url, init),
    openStream(spec) {
      onStream?.(spec);
      spec.onStatus("open");
      return { close() { spec.onStatus("closed"); } };
    },
  };
}
