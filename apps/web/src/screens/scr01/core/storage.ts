import type { Limits } from "./model";
import { DEFAULT_LIMITS } from "./pending";

export const THREAD_KEY = "mhc.chat.thread"; // sessionStorage; per tab (N-31)
export interface StoredThread { threadId: string; limits: Limits }

export function loadThread(): StoredThread | null {
  try {
    const raw = window.sessionStorage.getItem(THREAD_KEY);
    if (!raw) return null;
    const v = JSON.parse(raw) as { threadId?: unknown; limits?: Partial<Limits> | null };
    if (typeof v.threadId !== "string" || v.threadId === "") return null;
    return { threadId: v.threadId, limits: { ...DEFAULT_LIMITS, ...(v.limits ?? {}) } };
  } catch {
    return null;
  }
}
export function saveThread(v: StoredThread): void {
  try { window.sessionStorage.setItem(THREAD_KEY, JSON.stringify(v)); } catch { /* storage unavailable */ }
}
export function clearThread(): void {
  try { window.sessionStorage.removeItem(THREAD_KEY); } catch { /* storage unavailable */ }
}
