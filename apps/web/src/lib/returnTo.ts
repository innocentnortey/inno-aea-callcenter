/** Only same-origin relative paths survive; anything else becomes "/". */
export function safeReturnTo(value: string | null | undefined): string {
  if (!value) return "/";
  if (!/^\/(?![/\\])/.test(value)) return "/";
  // eslint-disable-next-line no-control-regex -- rejecting control characters is the point
  if (/[\x00-\x1f]/.test(value)) return "/";
  return value;
}
