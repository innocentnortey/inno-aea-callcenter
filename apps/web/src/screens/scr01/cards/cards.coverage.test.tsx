import { beforeEach, describe, expect, it } from "vitest";
import type { ReplyBlock } from "../contract";
import { expectNo24HourTimes } from "@/test/no24h";
import { FIXTURE_IDS } from "@/dev/scenarios/scr01-cards.fixtures";
import { cardRenderers, blockLayout } from "./index";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { STATE_MAP } from "./testing/stateMap";
import { chatThreadExample, handoffExample, schemaBlockTypes, turnExample, turnExampleNames } from "./testing/examples";

beforeEach(resetCardState);

describe("card coverage", () => {
  it("every block type has a renderer", () => {
    expect(Object.keys(cardRenderers).sort()).toEqual(schemaBlockTypes().sort());
    expect(schemaBlockTypes()).toHaveLength(24);
  });

  it("every named turn example renders through the registry without throwing", () => {
    const names = turnExampleNames();
    expect(names).toHaveLength(37);
    for (const name of names) {
      const res = turnExample(name);
      for (const block of res.blocks) {
        const render = cardRenderers[block.type] as (p: unknown) => React.ReactNode;
        const { container, unmount } = renderCard(<>{render(makeProps(block as never, { settled: res.settled }))}</>);
        expect(container.textContent, `${name}/${block.type}`).not.toContain("Unsupported block");
        expectNo24HourTimes(container);
        expect(container.textContent).not.toMatch(/\bcharged\b/i);
        unmount();
      }
    }
  });

  it("the state map names sources that exist", () => {
    const examples = new Set(turnExampleNames());
    for (const row of STATE_MAP) {
      const s = row.source;
      if ("example" in s) expect(examples.has(s.example), row.id).toBe(true);
      else if ("fixture" in s) expect(Object.keys(FIXTURE_IDS), row.id).toContain(s.fixture);
      else if ("handoff" in s) expect(handoffExample(s.handoff as "CASE_CREATED")).toBeTruthy();
      else if ("thread" in s) expect(chatThreadExample(s.thread as "ENDED_BLOCK")).toBeTruthy();
    }
    for (const type of schemaBlockTypes()) expect(STATE_MAP.some((r) => r.block === type), type).toBe(true);
  });

  it("blockLayout gives one of four values and pins the safety card", () => {
    for (const name of turnExampleNames()) {
      for (const b of turnExample(name).blocks as ReplyBlock[]) {
        expect(["bubble", "card", "pinned", "event"]).toContain(blockLayout(b));
        if (b.type === "safety") expect(blockLayout(b)).toBe("pinned");
      }
    }
  });
});
