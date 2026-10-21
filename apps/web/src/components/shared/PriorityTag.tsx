import type { components } from "@/api/types.gen";
import { Tag } from "@/components/ui/Tag";
import { IconWarning } from "@/components/ui/icons";

export function PriorityTag({ priority }: { priority: components["schemas"]["Priority"] }) {
  const strong = priority.level === "P0" || priority.level === "P1";
  return (
    <Tag tone={strong ? "strong" : "plain"} icon={strong ? <IconWarning size={14} strokeWidth={1.8} aria-hidden="true" /> : undefined}>
      {priority.level} {"·"} {priority.word}
    </Tag>
  );
}
