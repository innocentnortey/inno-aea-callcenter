import { vi } from "vitest";

export function mockDesktop(matches = true): void {
  vi.spyOn(window, "matchMedia").mockImplementation(
    (q: string) =>
      ({
        matches, media: q, onchange: null, addEventListener() {}, removeEventListener() {},
        addListener() {}, removeListener() {}, dispatchEvent: () => false,
      }) as MediaQueryList,
  );
}
