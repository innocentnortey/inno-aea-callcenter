import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "./Button";

describe("Button", () => {
  it("renders the four variants", () => {
    render(<><Button variant="primary">P</Button><Button>S</Button><Button variant="send">Se</Button><Button variant="text">T</Button></>);
    expect(screen.getAllByRole("button")).toHaveLength(4);
    expect(screen.getByRole("button", { name: "P" }).className).toContain("btn-primary-bg");
    expect(screen.getByRole("button", { name: "Se" }).className).toContain("btn-send-bg");
  });
  it("loading keeps the label, is disabled and aria-busy", async () => {
    const onClick = vi.fn();
    render(<Button loading onClick={onClick}>Save</Button>);
    const b = screen.getByRole("button", { name: "Save" });
    expect(b.getAttribute("aria-busy")).toBe("true");
    expect(b.hasAttribute("disabled")).toBe(true);
    await userEvent.click(b);
    expect(onClick).not.toHaveBeenCalled();
  });
  it("is disabled when asked and uses density heights", () => {
    render(<><Button disabled>D</Button><Button density="console">C</Button></>);
    expect(screen.getByRole("button", { name: "D" }).hasAttribute("disabled")).toBe(true);
    expect(screen.getByRole("button", { name: "C" }).className).toContain("control-h-console");
  });
});
