import { Button } from "@/components/ui";
import type { BlockProps } from "../contract";
import { InlineNotice } from "./parts/CardParts";

export function SessionEndedCard({ block, dispatch }: BlockProps<"session_ended">) {
  return (
    <div className="space-y-2 text-center">
      <InlineNotice>{block.text}</InlineNotice>
      <Button variant="primary" onClick={() => void dispatch({ kind: "newChat" })}>{block.new_chat_action}</Button>
    </div>
  );
}
