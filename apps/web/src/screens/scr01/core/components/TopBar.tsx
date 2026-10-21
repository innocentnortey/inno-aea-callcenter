import { Link } from "react-router";
import { screenById } from "@/routes";
import { RefChip } from "@/components/shared/RefChip";
import { AssistantMark } from "@/components/shared/marks";
import type { ChatState } from "../model";

/** R1. The brand is the page h1. The back button of design 8.1 is omitted: SCR-1 is home. */
export function TopBar({ replying, reference }: { replying: ChatState["replying"]; reference: string | null }) {
  const human = replying.kind === "human";
  return (
    <div className="flex items-center gap-3 px-3.5 py-3">
      <AssistantMark size={30} />
      <div className="min-w-0 flex-1">
        <h1 className="t-name">Meridian Home Comfort</h1>
        <p className="text-small text-text-muted">
          {human ? (
            `${replying.display_name ?? "A representative"} (demo representative). Assistant paused.`
          ) : (
            <>
              Meridian assistant {"·"} automated
              {reference ? (<>{" · "}<RefChip reference={reference} /></>) : null}
            </>
          )}
        </p>
      </div>
      <Link to={screenById("SCR-3").path} className="motion-control inline-flex min-h-[var(--target-min)] items-center px-1 text-ui font-semibold link-text">
        Demo guide
      </Link>
    </div>
  );
}
