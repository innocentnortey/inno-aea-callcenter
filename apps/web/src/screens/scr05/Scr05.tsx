import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { toApiError } from "@/api/errors";
import { AppFrame } from "@/components/shell/AppFrame";
import { ConsoleHeader, Main } from "@/components/shell/chrome";
import { RoleGate } from "@/components/shell/RoleGate";
import { EmptyState, ErrorLine, StaleLine } from "@/components/shared/states";
import { Kbd, Skeleton } from "@/components/ui";
import { caseHref, screenById } from "@/routes";
import { useSession } from "@/state/session";
import { ActionResult } from "../scr06/ActionResult";
import { ClaimedNotJoinedError, claimAndJoin } from "../scr06/claimAndJoin";
import { CLAIMED_NOT_JOINED_QUEUE, errorText } from "../scr06/errorCopy";
import { LiveQueueSection, NeedsActionSection } from "./QueueSections";
import { useQueueFeed } from "./useQueueFeed";
import { useRowKeys } from "./useRowKeys";

function QueueBody() {
  const navigate = useNavigate();
  const location = useLocation();
  const { role } = useSession();
  const feed = useQueueFeed();
  const [pendingRef, setPendingRef] = useState<string | null>(null);
  const [claimError, setClaimError] = useState<string | null>(null);
  const passed = (location.state as { resultLine?: string } | null)?.resultLine ?? null;
  const [resultLine, setResultLine] = useState<string | null>(passed);

  useEffect(() => {
    if (!passed) return;
    setResultLine(passed);
    const t = setTimeout(() => {
      setResultLine(null);
      navigate(".", { replace: true, state: null });
    }, 4000);
    return () => clearTimeout(t);
  }, [passed, navigate]);

  const open = (ref: string) => navigate(caseHref(ref));
  const onClaimAndJoin = async (ref: string) => {
    setPendingRef(ref);
    setClaimError(null);
    try {
      await claimAndJoin(ref);
      navigate(caseHref(ref));
    } catch (e) {
      if (e instanceof ClaimedNotJoinedError) {
        // The case is claimed now: say so, and refresh the queue so the row moves.
        setClaimError(CLAIMED_NOT_JOINED_QUEUE);
        feed.retry();
      } else {
        setClaimError(errorText(toApiError(e), "claim", role ?? "representative").text);
      }
    } finally {
      setPendingRef(null);
    }
  };

  const data = feed.shown;
  const refs = data ? [...data.live.map((r) => r.reference), ...data.needs_my_action.map((r) => r.reference)] : [];
  const { cursor } = useRowKeys(refs, { onOpen: open, enabled: true });

  return (
    <div className="flex flex-col gap-4">
      {resultLine ? <ActionResult id="queue-result">{resultLine}</ActionResult> : null}
      {claimError ? <p className="text-ui" role="status">{claimError}</p> : null}
      {feed.changedCount > 0 ? (
        <StaleLine actionLabel="Show them" onAction={feed.showChanged}>
          {feed.changedCount === 1 ? "1 case changed." : `${feed.changedCount} cases changed.`}
        </StaleLine>
      ) : null}
      {!data && feed.status === "error" ? (
        <ErrorLine message="The queue didn't load. Try again." onRetry={feed.retry} />
      ) : !data ? (
        <Skeleton height={44} rows={5} />
      ) : (
        <>
          <LiveQueueSection
            staffing={data.staffing} rows={data.live} cursor={cursor} onOpen={open}
            onClaimAndJoin={(r) => void onClaimAndJoin(r)} pendingRef={pendingRef}
          />
          {data.needs_my_action.length === 0 && data.live.length === 0 ? (
            <EmptyState title="You're all caught up." body="No case needs your action. New handoffs from the chat appear here." />
          ) : (
            <NeedsActionSection rows={data.needs_my_action} cursor={cursor} onOpen={open} />
          )}
          <p className="hidden text-small text-text-muted min-[1100px]:block"><Kbd>J</Kbd> / <Kbd>K</Kbd> to move, <Kbd>Enter</Kbd> to open</p>
        </>
      )}
    </div>
  );
}

export default function Scr05() {
  const def = screenById("SCR-5");
  useEffect(() => { document.title = `${def.id} · ${def.title} · Meridian`; }, [def]);
  return (
    <AppFrame variant="console">
      <ConsoleHeader />
      <Main className="flex flex-col gap-4 p-4">
        <h1 className="t-title">Representative queue</h1>
        <RoleGate allow={def.roles}>
          <QueueBody />
        </RoleGate>
      </Main>
    </AppFrame>
  );
}
