// FROZEN by the foundation slice. G1's thread calls renderBlock(); G2 fills ./cards.
import type { ReactNode } from "react";
import type { BlockProps, BlockRenderer, BlockType } from "./contract";
import { cardRenderers } from "./cards";

export function renderBlock(props: BlockProps<BlockType>): ReactNode {
  const renderer = cardRenderers[props.block.type] as BlockRenderer<BlockType> | undefined;
  if (!renderer) return <p className="text-small text-text-muted">Unsupported block: {props.block.type}</p>;
  return renderer(props);
}
