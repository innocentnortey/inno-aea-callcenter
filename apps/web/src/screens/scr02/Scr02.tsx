import { useEffect, type MouseEvent } from "react";
import { Link } from "react-router";
import { AppFrame } from "@/components/shell/AppFrame";
import { DemoPageHeader, Main } from "@/components/shell/chrome";
import { EmptyState, ErrorLine } from "@/components/shared/states";
import { Skeleton } from "@/components/ui";
import { InboxList } from "./InboxList";
import { useCopyCode } from "./useCopyCode";
import { useInbox } from "./useInbox";
import { BACK, EMPTY_BODY, EMPTY_TITLE, ERROR, FOOT, H1, HEADER_TITLE, STATEMENT } from "./copy";

/** Switches to the opener tab when there is one; otherwise the link opens the chat at "/". */
function BackToChat() {
  const onClick = (e: MouseEvent) => {
    const opener = window.opener as Window | null;
    if (opener && !opener.closed) {
      e.preventDefault();
      try { opener.focus(); } catch { /* the link still reads as handled */ }
    }
  };
  return <Link to="/" onClick={onClick} className="link-text">{BACK}</Link>;
}

export default function Scr02() {
  const { messages, phase, refetch } = useInbox();
  const { copiedId, failedId, copy } = useCopyCode();
  useEffect(() => { document.title = "SCR-2 · Demo delivery inbox · Meridian"; }, []);

  return (
    <AppFrame variant="page">
      <DemoPageHeader title={HEADER_TITLE} showDemoBar />
      <Main className="p-4">
        <h1 className="t-title">{H1}</h1>
        <p className="mt-2 text-body">{STATEMENT}</p>
        {phase === "loading" ? (
          <div data-testid="inbox-loading" aria-busy="true" className="mt-4"><Skeleton height={132} /></div>
        ) : null}
        {phase === "error" ? <ErrorLine className="mt-4" message={ERROR} onRetry={() => void refetch()} /> : null}
        {phase === "empty" ? <EmptyState title={EMPTY_TITLE} body={EMPTY_BODY} action={<span className="mt-2"><BackToChat /></span>} /> : null}
        {phase === "list" ? <InboxList messages={messages} copiedId={copiedId} failedId={failedId} onCopy={(id, code) => void copy(id, code)} /> : null}
        <footer className="mt-6 flex flex-col gap-2">
          <p className="text-small text-text-muted">{FOOT}</p>
          {phase !== "empty" ? <p><BackToChat /></p> : null}
        </footer>
      </Main>
    </AppFrame>
  );
}
