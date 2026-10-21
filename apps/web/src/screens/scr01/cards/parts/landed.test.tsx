import { beforeEach, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { StrictMode } from "react";
import { resetLandedForTests, useLandedOnce } from "./landed";

function Probe({ id, props }: { id: string; props: { landed(t: "visit" | "request" | "identity"): void; announce(m: string): void } }) {
  useLandedOnce(id, "visit", "msg", props);
  return null;
}
beforeEach(resetLandedForTests);

describe("useLandedOnce", () => {
  it("fires once per block id, even when remounted", () => {
    const props = { landed: vi.fn(), announce: vi.fn() };
    const a = render(<StrictMode><Probe id="b1" props={props} /></StrictMode>);
    a.unmount();
    render(<Probe id="b1" props={props} />);
    expect(props.landed).toHaveBeenCalledTimes(1);
    expect(props.landed).toHaveBeenCalledWith("visit");
    expect(props.announce).toHaveBeenCalledTimes(1);
  });
});
