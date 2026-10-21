import { renderBlock } from "../../blocks";
import type { BlockOf, BlockProps } from "../../contract";

/** R5: the DANGER card, above the log, never dismissible. The parent keys it by block_id so it mounts once. */
export function PinnedSafety({ block, ...props }: { block: BlockOf<"safety"> } & Omit<BlockProps<"safety">, "block">) {
  return (
    // A plain wrapper: G2's card carries its own named section, so a second landmark of the same name would be a duplicate.
    <div data-pinned-safety className="flex-none px-3.5 pb-2 pt-3">
      {renderBlock({ block, ...props })}
    </div>
  );
}
