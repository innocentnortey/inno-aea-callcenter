export type Theme = "light" | "dark";
const KEY = "mhc.theme";
export function readTheme(): Theme {
  try {
    const v = localStorage.getItem(KEY);
    return v === "dark" || v === "light" ? v : "light";
  } catch {
    return "light";
  }
}
/** Light is the default whatever the system setting is; dark is chosen on purpose. */
export function applyTheme(): void {
  document.documentElement.dataset.theme = readTheme();
}
export function setTheme(t: Theme): void {
  try {
    localStorage.setItem(KEY, t);
  } catch {
    /* storage unavailable: the choice lasts until reload */
  }
  document.documentElement.dataset.theme = t;
}
