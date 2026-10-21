import type { DirectorRule } from "../scenarios/types";

// Reviewer phrases that trigger server-side conditions in free play (dev layer only). Gas and carbon-monoxide words are
// left to G2's keyword rules (G1-e); card ids and the `demo:` prefix are G2's too.
const PHRASES: [RegExp, string][] = [
  [/^\s*test:\s*rate limit/i, "RATE_LIMITED"],
  [/^\s*test:\s*booking cap/i, "BOOKING_CAP"],
  [/^\s*test:\s*spend cap/i, "SPEND_CAP_REACHED"],
  [/^\s*test:\s*timeout/i, "TURN_TIMEOUT"],
  [/^\s*test:\s*busy/i, "BUSY"],
  [/^\s*test:\s*paused/i, "AI_PAUSED"],
];
export const rules: DirectorRule[] = [
  (req) => {
    if (req.payload.kind !== "text") return undefined;
    const text = req.payload.text;
    return PHRASES.find(([re]) => re.test(text))?.[1];
  },
];
