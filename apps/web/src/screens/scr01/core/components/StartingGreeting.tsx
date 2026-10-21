import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui";
import { ErrorLine } from "@/components/shared/states";

/** Session start: a one-line skeleton for the first second, then words. */
export function StartingGreeting({ phase, message, onRetry }: { phase: "starting" | "start-failed"; message: string | null; onRetry: () => void }) {
  const [late, setLate] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setLate(true), 1000);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="min-h-0 flex-1 px-3.5 py-4">
      {phase === "start-failed" ? (
        <ErrorLine message={message ?? "The chat didn't start. Try again."} onRetry={onRetry} />
      ) : late ? (
        <p role="status" className="text-body">Starting the chat{"…"}</p>
      ) : (
        <Skeleton height={24} />
      )}
    </div>
  );
}
