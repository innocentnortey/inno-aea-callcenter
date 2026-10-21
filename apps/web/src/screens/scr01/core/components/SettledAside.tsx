import { Disclosure } from "@/components/ui";
import type { Settled } from "../../contract";
import type { ChatState } from "../model";
import { stripLine, type LandTarget } from "../settledSummary";
import { useMediaQuery, WIDE } from "../useMediaQuery";
import { SettledPanel } from "./SettledPanel";

export interface SettledAsideProps {
  settled: Settled | null; danger: boolean; replying: ChatState["replying"]; staffingOn: boolean;
  landing: { target: LandTarget; nonce: number } | null;
}
/** R4: the strip under the top bar on phones, the always-open panel from 900 px. One aside, one name. */
export function SettledAside(props: SettledAsideProps) {
  const wide = useMediaQuery(WIDE);
  return (
    <aside
      aria-label="What's settled"
      className="flex-none min-[900px]:order-2 min-[900px]:w-[var(--panel-width)] min-[900px]:overflow-y-auto min-[900px]:border-l min-[900px]:border-border-hair min-[900px]:bg-[var(--rail-bg)]"
    >
      {wide ? (
        <SettledPanel {...props} />
      ) : (
        <div className="border-b border-[color:var(--strip-rule)] bg-[var(--strip-bg)]">
          <Disclosure
            className="px-3.5"
            summary={
              <span className="flex min-w-0 items-baseline gap-2 text-small">
                <span className="font-semibold">{"What's settled"}</span>
                <span className="min-w-0 truncate tabular-nums" data-testid="strip-line">{stripLine(props.settled, props.danger)}</span>
              </span>
            }
          >
            <div className="max-h-[52vh] overflow-y-auto"><SettledPanel {...props} /></div>
          </Disclosure>
        </div>
      )}
    </aside>
  );
}
