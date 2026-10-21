import { useEffect } from "react";
import { AppFrame } from "@/components/shell/AppFrame";
import { Main } from "@/components/shell/chrome";
import { LiveRegion } from "@/components/ui";
import { useDemoStatus } from "@/state/demoStatus";
import "./core/chat.css";
import { ChatHeader } from "./core/components/ChatHeader";
import { Composer } from "./core/components/Composer";
import { PinnedSafety } from "./core/components/PinnedSafety";
import { SettledAside } from "./core/components/SettledAside";
import { StartingGreeting } from "./core/components/StartingGreeting";
import { Thread } from "./core/components/Thread";
import { findPinnedSafety } from "./core/replyGroups";
import { useChat } from "./core/useChat";

/** SCR-1: the customer chat. G1 owns the shell and plumbing; every reply block is drawn by G2's renderBlock. */
export default function Scr01() {
  const chat = useChat();
  const { staffing } = useDemoStatus();
  const { state } = chat;
  useEffect(() => { document.title = "SCR-1 · Customer chat · Meridian"; }, []);
  const pinned = findPinnedSafety(state.entries);
  const disabled = state.ended !== null || state.pending !== null;
  const shared = { settled: state.settled, dispatch: chat.dispatch, announce: chat.announce, landed: chat.land };
  return (
    <AppFrame variant="chat">
      <div data-screen="SCR-1" className="flex h-[100dvh] max-h-[900px] flex-col bg-[var(--app-bg)] min-[700px]:h-[calc(100dvh-48px)]">
        <ChatHeader replying={state.replying} reference={state.settled?.request?.reference ?? null} streamStatus={chat.streamStatus} />
        <div className="flex min-h-0 flex-1 flex-col min-[900px]:flex-row">
          <SettledAside settled={state.settled} danger={pinned !== null} replying={state.replying} staffingOn={staffing?.mode === "simulated_on_shift"} landing={chat.landing} />
          <Main className="flex min-h-0 flex-1 flex-col min-[900px]:order-1">
            {pinned ? <PinnedSafety key={pinned.block_id} block={pinned} answered={false} disabled={disabled} {...shared} /> : null}
            {state.phase === "ready" ? (
              <Thread
                entries={state.entries} answered={state.answered} disabled={disabled} phase={chat.phase}
                scrollTarget={chat.scrollTarget} onRetry={(turnId) => void chat.dispatch({ kind: "retry", turnId })} {...shared}
              />
            ) : (
              <StartingGreeting phase={state.phase} message={state.startFailure} onRetry={chat.retryStart} />
            )}
            <Composer lock={chat.composerLock} pending={state.pending !== null} replying={state.replying} limits={state.limits} dispatch={chat.dispatch} canSend={chat.canSend} />
          </Main>
        </div>
        <LiveRegion politeness="polite">{chat.landingText}</LiveRegion>
      </div>
    </AppFrame>
  );
}
