import { expect } from "vitest";
/** Fails if the container's text holds a clock time without am/pm (24-hour style). */
export function expectNo24HourTimes(container: HTMLElement): void {
  const text = container.textContent ?? "";
  expect(text).not.toMatch(/\b(?:[01]?\d|2[0-3]):[0-5]\d\b(?!\s?[ap]m)/i);
}
