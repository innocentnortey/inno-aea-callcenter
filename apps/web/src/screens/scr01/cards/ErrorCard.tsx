import type { BlockProps } from "../contract";
import { InlineNotice, PersonKey } from "./parts/CardParts";
import { SlotCard } from "./SlotCard";

export function ErrorCard(props: BlockProps<"error">) {
  const { block } = props;
  switch (block.code) {
    case "CODE_WRONG":
    case "CODE_EXPIRED":
      return <InlineNotice role="alert">{block.text}</InlineNotice>;
    case "SLOT_TAKEN":
      return (
        <div className="space-y-3">
          <InlineNotice role="status">{block.text}</InlineNotice>
          {block.fresh_windows ? <SlotCard {...props} block={block.fresh_windows} /> : null}
        </div>
      );
    default:
      // OUT_OF_AREA, CODE_LOCKED, CODE_CAP_REACHED, NOT_VERIFIED: one shared structure, no code-specific markup,
      // so the three identity outcomes cannot be told apart (no account-existence leak).
      return (
        <div className="space-y-2">
          <InlineNotice role="status">{block.text}</InlineNotice>
          {block.person_key ? <PersonKey dispatch={props.dispatch} /> : null}
        </div>
      );
  }
}
