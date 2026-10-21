import { useEventStream } from "@/api/useEventStream";
import type { StreamStatus } from "@/api/transport";
import type { components } from "@/api/types.gen";
import { useAnnounce } from "@/components/ui";
import type { CaseAction } from "./caseReducer";

export function useCaseStream(reference: string | undefined, enabled: boolean, dispatch: (a: CaseAction) => void): { status: StreamStatus } {
  const announce = useAnnounce();
  const { status } = useEventStream(
    enabled && reference ? { op: "streamCaseEvents", path: { reference } } : null,
    (data) => {
      const ev = data as components["schemas"]["CaseEvent"];
      if (!ev || typeof ev !== "object" || !("type" in ev)) return;
      dispatch({ type: "stream", event: ev });
      if (ev.type === "customer_message") announce("Customer: " + ev.message.text);
    },
  );
  return { status };
}
