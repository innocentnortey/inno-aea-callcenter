import { beforeEach, describe, expect, it } from "vitest";
import { applyTheme, setTheme } from "./theme";

describe("theme", () => {
  beforeEach(() => { localStorage.clear(); delete document.documentElement.dataset.theme; });
  it("defaults to light", () => { applyTheme(); expect(document.documentElement.dataset.theme).toBe("light"); });
  it("stored dark wins", () => { localStorage.setItem("mhc.theme", "dark"); applyTheme(); expect(document.documentElement.dataset.theme).toBe("dark"); });
  it("ignores junk", () => { localStorage.setItem("mhc.theme", "purple"); applyTheme(); expect(document.documentElement.dataset.theme).toBe("light"); });
  it("setTheme stores and applies", () => { setTheme("dark"); expect(localStorage.getItem("mhc.theme")).toBe("dark"); expect(document.documentElement.dataset.theme).toBe("dark"); });
});
