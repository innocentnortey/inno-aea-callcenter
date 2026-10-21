/** UXR-19: "{promise_text}, {due_label}. {extra_lines...}". `omit` removes lines shown elsewhere (exact string match). */
export function joinPromise(
  p: { promise_text: string; due_label: string | null; extra_lines: string[] },
  omit?: Array<string | null>,
): string {
  let lead = p.due_label ? `${p.promise_text}, ${p.due_label}.` : p.promise_text;
  if (!/[.!?]$/.test(lead)) lead += ".";
  const lines = p.extra_lines.filter((l) => !omit?.includes(l));
  return [lead, ...lines].join(" ");
}
