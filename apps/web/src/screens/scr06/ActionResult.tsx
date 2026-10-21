import type { ReactNode } from "react";
import { ResultLine } from "@/components/shared/states";

/** The success line. Focus moves here after every successful action. */
export function ActionResult({ id, children }: { id: string; children: ReactNode }) {
  return (
    <div id={id} tabIndex={-1} className="outline-none">
      <ResultLine>{children}</ResultLine>
    </div>
  );
}
export function focusResult(id: string): void {
  setTimeout(() => document.getElementById(id)?.focus(), 0);
}
