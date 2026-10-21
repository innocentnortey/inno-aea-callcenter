import type { Reaction } from "../scenarios/types";

export const reactions: Reaction[] = [
  // After a demo reset the stored thread reads as ended, as the real backend does.
  { when: { op: "resetDemo", status: 200 }, then(ctx) { ctx.setForce("getChatThread", { example: "SESSION_ENDED", status: 410 }); } },
  // A new chat clears that force.
  { when: { op: "startChatSession", status: 201 }, then(ctx) { ctx.setForce("getChatThread", null); } },
];
