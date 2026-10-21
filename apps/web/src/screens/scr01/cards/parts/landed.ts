import { useEffect } from "react";

export type LandProps = { landed(t: "visit" | "request" | "identity"): void; announce(m: string): void };
const seen = new Set<string>();

/** On the first mount per block_id: props.landed(target) then props.announce(message). Remounts do nothing. */
export function useLandedOnce(blockId: string, target: "visit" | "request" | "identity", message: string, props: LandProps): void {
  const { landed, announce } = props;
  useEffect(() => {
    if (seen.has(blockId)) return;
    seen.add(blockId);
    landed(target);
    announce(message);
    // once per block_id by design
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
/** Forget which blocks already landed (new chat, demo reset). */
export function resetLanded(): void { seen.clear(); }
export const resetLandedForTests = resetLanded;
