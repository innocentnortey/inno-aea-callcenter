const rendered = new Map<string, Set<string>>();

export function markChipRendered(at: string, passageId: string): void {
  const set = rendered.get(at) ?? new Set<string>();
  set.add(passageId);
  rendered.set(at, set);
}
export function chipAlreadyRendered(at: string, passageId: string): boolean {
  return rendered.get(at)?.has(passageId) ?? false;
}
export function resetDedupeForTests(): void { rendered.clear(); }
