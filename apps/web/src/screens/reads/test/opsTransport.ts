import type { ApiTransport, CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { makeFakeTransport } from "@/test/fakeTransport";
import { shellTransport } from "@/test/render";

export type OpHandler = (ctx: CallContext) => Response | Promise<Response>;
/** The shell's own reads answer as usual; handlers answer the screen's operations. Every call is recorded. */
export function opsTransport(role: Role | null, handlers: Record<string, OpHandler>, calls: CallContext[] = []): ApiTransport {
  const shell = shellTransport(role);
  return makeFakeTransport((ctx, url, init) => {
    calls.push(ctx);
    const h = handlers[ctx.op];
    return h ? h(ctx) : shell.fetch(ctx, url, init);
  });
}
