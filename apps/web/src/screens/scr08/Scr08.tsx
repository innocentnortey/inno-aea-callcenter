import { useState } from "react";
import { ApiError } from "@/api/errors";
import type { components } from "@/api/types.gen";
import { useAction, useOp } from "@/api/useOp";
import { EmptyState, ResultLine, StaleLine } from "@/components/shared/states";
import { AppFrame } from "@/components/shell/AppFrame";
import { ConsoleHeader, Main } from "@/components/shell/chrome";
import { RoleGate } from "@/components/shell/RoleGate";
import { Skeleton } from "@/components/ui";
import { useAnnounce } from "@/components/ui/LiveRegion";
import { useSession } from "@/state/session";
import { pluralize } from "../reads/format";
import { ReadError } from "../reads/ReadError";
import { ScreenTitle } from "../reads/ScreenTitle";
import { FlagsTable } from "./FlagsTable";
import { useShownFlags } from "./useShownFlags";

type Flag = components["schemas"]["Flag"];
type Patch = Pick<Flag, "status" | "reviewed_by" | "reviewed_note">;
const HINT = "Supervisors mark flags reviewed.";

export default function Scr08() {
  return (
    <AppFrame variant="console">
      <ConsoleHeader />
      <Main className="flex flex-col gap-4 p-4">
        <ScreenTitle id="SCR-8">Review list of flags</ScreenTitle>
        <RoleGate allow={["representative", "supervisor", "owner"]}><Flags /></RoleGate>
      </Main>
    </AppFrame>
  );
}

function Flags() {
  const { role } = useSession();
  const announce = useAnnounce();
  const res = useOp("listFlags", {}, { pollMs: 15_000, refetchOnFocus: true });
  const { shown, newCount, showNew } = useShownFlags(res.data?.flags);
  const review = useAction("reviewFlag");
  const [editing, setEditing] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [rowError, setRowError] = useState<{ id: string; message: string } | null>(null);
  const [patches, setPatches] = useState<Record<string, Patch>>({});
  const [resultLine, setResultLine] = useState("");
  const canReview = role === "supervisor";

  async function onReview(flag: Flag, note: string | null) {
    setPendingId(flag.flag_id);
    setRowError(null);
    try {
      const r = await review.run({ path: { flag_id: flag.flag_id }, body: { status: "reviewed", note } });
      setPatches((p) => ({ ...p, [flag.flag_id]: { status: "reviewed", reviewed_by: r.reviewed_by, reviewed_note: r.reviewed_note } }));
      setEditing(null);
      setResultLine("Marked reviewed.");
      announce("Marked reviewed.");
      setTimeout(() => document.getElementById("flags-result")?.focus(), 0);
      void res.refetch();
    } catch (e) {
      const err = e instanceof ApiError ? e : null;
      if (err?.isRoleNotAllowed) setRowError({ id: flag.flag_id, message: HINT });
      else if (err?.code === "FLAG_NOT_FOUND") {
        setRowError({ id: flag.flag_id, message: "That flag is gone. It may have been cleared by a demo reset." });
        void res.refetch();
      } else setRowError({ id: flag.flag_id, message: "Couldn't mark it reviewed. Try again." });
    } finally {
      setPendingId(null);
    }
  }

  let body;
  if (res.data === undefined && res.error) {
    body = <ReadError error={res.error} role={role} allow={["representative", "supervisor", "owner"]} didntLoad="The review list didn't load. Try again." onRetry={() => void res.refetch()} />;
  } else if (res.data === undefined) {
    body = <Skeleton height={44} rows={4} />;
  } else if (res.data.flags.length === 0 && shown.length === 0) {
    body = <EmptyState title="No flags yet." body="Staff flag a wrong answer, a brief that left something out, or an escalation that wasn't needed, from any case." />;
  } else {
    body = (
      <>
        {newCount > 0 ? (
          <StaleLine actionLabel={newCount === 1 ? "Show it" : "Show them"} onAction={showNew}>
            {`${newCount} new ${pluralize(newCount, "flag", "flags")} since you opened this page.`}
          </StaleLine>
        ) : null}
        <FlagsTable
          flags={shown.map((f) => ({ ...f, ...patches[f.flag_id] }))}
          canReview={canReview} hintId="flags-hint" editing={editing} onEdit={setEditing}
          onReview={onReview} pendingId={pendingId} rowError={rowError}
        />
        {resultLine ? <ResultLine id="flags-result">{resultLine}</ResultLine> : null}
      </>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      <p className="text-ui">Nothing on this list changes the knowledge base, prompts or tests. People decide each fix.</p>
      {!canReview ? <p id="flags-hint" className="text-ui">{HINT}</p> : null}
      {body}
    </div>
  );
}
