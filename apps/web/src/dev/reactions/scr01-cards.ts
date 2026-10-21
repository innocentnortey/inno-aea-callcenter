import type { Reaction } from "../scenarios/types";

const SLUG = "scr01-cards";

export const reactions: Reaction[] = [
  // A forced next reply is consumed by that reply (a sequence keeps its own cursor).
  {
    when: { op: "submitTurn" },
    then(ctx) {
      const f = ctx.world.forces.submitTurn;
      if (ctx.world.scenarioId?.startsWith(`${SLUG}.`) && f && "example" in f) ctx.setForce("submitTurn", null);
    },
  },
  // A second "Talk to a person" tap answers ALREADY_OPEN.
  { when: { op: "requestPerson", example: "CASE_CREATED" }, then: (ctx) => ctx.setForce("requestPerson", { example: "ALREADY_OPEN" }) },
  { when: { op: "requestPerson", example: "LIVE_QUEUED" }, then: (ctx) => ctx.setForce("requestPerson", { example: "ALREADY_OPEN" }) },
  { when: { op: "resetDemo" }, then: (ctx) => { ctx.setForce("requestPerson", null); ctx.setForce("submitTurn", null); } },
  { when: { op: "startChatSession" }, then: (ctx) => ctx.setForce("requestPerson", null) },
];
