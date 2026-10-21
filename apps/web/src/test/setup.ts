import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => cleanup());

// jsdom has no <dialog> methods, matchMedia, scrollIntoView or clipboard.
if (typeof HTMLDialogElement !== "undefined") {
  HTMLDialogElement.prototype.showModal ||= function (this: HTMLDialogElement) { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close ||= function (this: HTMLDialogElement) { this.removeAttribute("open"); this.dispatchEvent(new Event("close")); };
}
if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false, media: query, onchange: null, addEventListener: () => {}, removeEventListener: () => {},
    addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
Element.prototype.scrollIntoView ||= vi.fn();
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// react-router builds Node (undici) Requests with jsdom AbortSignals, which undici rejects. Signals are dropped in tests.
const NodeRequest = globalThis.Request;
globalThis.Request = class extends NodeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    const rest = init ? { ...init } : init;
    if (rest) delete rest.signal;
    super(input, rest);
  }
} as typeof Request;
