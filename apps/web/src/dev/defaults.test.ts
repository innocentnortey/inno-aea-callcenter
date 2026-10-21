import { beforeEach, describe, expect, it } from "vitest";
import { OPS } from "@/api/client";
import { defaultExample } from "./defaults";
import { getWorld, resetWorld, setWorld } from "./world";

beforeEach(() => { sessionStorage.clear(); resetWorld(); });

describe("defaultExample requestPerson", () => {
  it("answers LIVE_QUEUED when simulated staff are on shift", () => {
    setWorld({ staffing: "simulated_on_shift" });
    expect(defaultExample("requestPerson", getWorld())).toBe("LIVE_QUEUED");
  });
  it("keeps the first 2xx example otherwise", () => {
    const first = OPS.requestPerson.responses.find((r) => r.status >= 200 && r.status < 300 && r.examples.length > 0)?.examples[0];
    expect(defaultExample("requestPerson", getWorld())).toBe(first);
    expect(first).not.toBe("LIVE_QUEUED");
  });
});
