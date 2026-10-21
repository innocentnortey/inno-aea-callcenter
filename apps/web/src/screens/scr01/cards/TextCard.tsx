import type { BlockProps } from "../contract";
import { SourceChipView } from "./SourceChipView";
import { chipAlreadyRendered, markChipRendered } from "./sourceDedupe";

export function TextCard({ block }: BlockProps<"text">) {
  for (const s of block.sources) markChipRendered(block.at, s.passage_id);
  return (
    <div>
      <p className="whitespace-pre-line text-body">{block.text}</p>
      {block.sources.map((s) => <SourceChipView key={s.passage_id} source={s} />)}
    </div>
  );
}
export function SourceChipCard({ block }: BlockProps<"source_chip">) {
  if (chipAlreadyRendered(block.at, block.source.passage_id)) return null;
  return <SourceChipView source={block.source} />;
}
