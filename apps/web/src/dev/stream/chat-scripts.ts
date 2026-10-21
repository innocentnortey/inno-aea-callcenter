// G1 scripted chat streams. Events are built from the typed factories in ./events (copies of the OpenAPI named examples:
// streamChatEvents FRAMES for representative_joined / ai_paused / staff_message; the rest are dev fixtures with no named example).
// event_id values start at 40 and rise within a script. Lines copy SCREEN_SPECS SCR-1 "Copy notes" and flow-state rows.
import type { components } from "@/api/types.gen";
import { chatEvents } from "./events";
import type { StreamScript } from "./types";

type ChatEvent = components["schemas"]["ChatEvent"];
const E = chatEvents;
const AT = "2026-10-16T14:22:00-05:00";
// The factories return the ChatEvent union, so overrides are applied untyped here; chat-scripts.test.ts checks the shapes.
const id = (event: object, n: number): ChatEvent => ({ ...event, event_id: n }) as ChatEvent;

const joins = (): StreamScript["steps"] => [
  { afterMs: 1500, event: id(E.representative_joined(), 40) },
  { afterMs: 1600, event: id(E.ai_paused(), 41) },
  { afterMs: 4000, event: id(E.staff_message(), 42) },
];

export const chatScripts: Record<string, StreamScript> = {
  "rep-joins": { steps: joins() },
  "rep-hands-back": {
    steps: [...joins(), { afterMs: 8000, event: id({ ...E.ai_resumed(), at: AT, line: "Riley handed the chat back to the automated assistant." }, 43) }],
  },
  "rep-closes": {
    steps: [...joins(), { afterMs: 8000, event: id({ ...E.chat_closed(), at: AT, line: "Riley closed this chat.", composer_disabled: true }, 43) }],
  },
  // handoff + settled copy submitTurn HANDOFF (same reference MHC-C-0007), via the shift_ended factory
  "shift-ends": {
    steps: [{ afterMs: 4000, event: id({ ...E.shift_ended(), line: "The simulated shift ended before a representative joined." }, 40) }],
  },
  // staffing bodies copy getStaffing ON / OFF
  "staffing-on": {
    steps: [{ afterMs: 2000, event: id({ ...E.staffing_changed(), line: "Staffing changed: simulated staff on shift (demo)." }, 40) }],
  },
  "staffing-off": {
    steps: [{
      afterMs: 2000,
      event: id({
        ...E.staffing_changed(),
        staffing: { mode: "nobody_online", label: "Nobody online", banner: null },
        line: "Staffing changed: nobody online.", // dev fixture: the spec gives only the "on" wording
      }, 40),
    }],
  },
  "clock-moves": { steps: [{ afterMs: 2000, event: id(E.clock_changed(), 40) }] },
  "demo-reset": {
    steps: [{ afterMs: 2500, event: id({ ...E.demo_reset(), line: "The demo was reset, so this chat has ended. Nothing from it was kept." }, 40) }],
  },
  // the connection drops, a message is buffered; the panel's Stream tab "Reconnect" replays it
  "drop-and-late": {
    dropAfterMs: 1500,
    steps: [{ afterMs: 6000, event: id({ ...E.staff_message(), message_id: "m-89", text: "Are you still there?" }, 40) }], // dev fixture
  },
};
