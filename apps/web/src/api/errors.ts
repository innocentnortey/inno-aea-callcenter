export class ApiError extends Error {
  constructor(
    public readonly status: number, // 0 = network failure
    public readonly code: string, // body.error.code, else "NETWORK" | "HTTP_<status>" | "CONTRACT_DRIFT"
    public readonly body: unknown,
    public readonly details: Record<string, unknown> | null = null,
    public readonly requestId: string | null = null,
    public readonly field: string | null = null,
  ) {
    super(code);
    this.name = "ApiError";
  }
  get isUnauthenticated() {
    return this.status === 401 && this.code === "UNAUTHENTICATED";
  }
  get isRoleNotAllowed() {
    return this.status === 403 && this.code === "ROLE_NOT_ALLOWED";
  }
}
/** Anything thrown by fetch becomes ApiError(0, "NETWORK"). */
export function toApiError(e: unknown): ApiError {
  if (e instanceof ApiError) return e;
  return new ApiError(0, "NETWORK", e instanceof Error ? e.message : String(e));
}
