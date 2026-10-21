import { EventLine } from "@/components/shared/messages";
import { IconCheck, IconClock, IconInfo, IconUser } from "@/components/ui";
import type { EventIcon } from "../model";
import type { Entry } from "../model";

const ICONS: Record<EventIcon, typeof IconInfo> = {
  joined: IconUser, paused: IconInfo, resumed: IconCheck, closed: IconInfo, shift: IconClock, reset: IconInfo, staffing: IconInfo,
};
export function EventEntry({ entry }: { entry: Extract<Entry, { kind: "event" }> }) {
  const Icon = ICONS[entry.icon];
  return (
    <EventLine className="chat-fade-in" icon={<Icon size={14} strokeWidth={1.8} aria-hidden="true" />} at={entry.at ?? undefined}>
      {entry.line}
    </EventLine>
  );
}
