import { DemoBar, SignOutButton, StaffingBanner } from "@/components/shell/chrome";
import { RoleSwitch } from "@/components/shell/RoleSwitch";
import { StaleLine } from "@/components/shared/states";
import type { ChatState } from "../model";
import type { StreamStatus } from "../useChat";
import { TopBar } from "./TopBar";

/** R1 to R3 plus the reconnecting line. The role row is always its own 44 px row, in every state (D3). */
export function ChatHeader({ replying, reference, streamStatus }: { replying: ChatState["replying"]; reference: string | null; streamStatus: StreamStatus }) {
  return (
    <header className="flex-none border-b border-border-hair bg-surface">
      <TopBar replying={replying} reference={reference} />
      <DemoBar />
      <div className="flex min-h-[44px] items-center justify-between gap-1 px-3.5">
        {/* Phone widths: tighter radios so the four roles and Sign out share the 44 px row at 390 px (the shared RoleSwitch is read-only here). */}
        <RoleSwitch
          variant="row"
          className="min-w-0 flex-1 max-[699px]:[&_[role=radio]]:px-1 max-[699px]:[&_[role=radio]]:text-small max-[699px]:[&_[role=radiogroup]]:gap-1"
        />
        <SignOutButton />
      </div>
      <StaffingBanner />
      {streamStatus === "reconnecting" ? (
        <StaleLine className="px-4 py-2">Reconnecting{"…"} Staffing and messages may be out of date.</StaleLine>
      ) : null}
    </header>
  );
}
