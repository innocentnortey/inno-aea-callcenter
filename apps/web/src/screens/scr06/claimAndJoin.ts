import { callOp, type OkBody } from "@/api/client";

/** The claim (CON-13) went through but the join (CON-14) did not: the case is now the caller's, the chat is not. */
export class ClaimedNotJoinedError extends Error {
  constructor(public readonly claim: OkBody<"applyCaseAction">, public readonly joinError: unknown) {
    super("claimed but not joined");
    this.name = "ClaimedNotJoinedError";
  }
}

/**
 * CON-13 claim, then CON-14 join, in that order. A failed claim throws its ApiError unchanged;
 * a failed join throws ClaimedNotJoinedError carrying the claim response, so callers can refresh what the claim changed.
 */
export async function claimAndJoin(
  reference: string,
  knownVersion?: number,
): Promise<{ claim: OkBody<"applyCaseAction">; join: OkBody<"liveChatAction"> }> {
  const version = knownVersion ?? (await callOp("getCase", { path: { reference } })).case.version;
  const claim = await callOp("applyCaseAction", { path: { reference }, body: { action: "claim", expected_version: version } });
  try {
    const join = await callOp("liveChatAction", { path: { reference }, body: { action: "join" } });
    return { claim, join };
  } catch (e) {
    throw new ClaimedNotJoinedError(claim, e);
  }
}
