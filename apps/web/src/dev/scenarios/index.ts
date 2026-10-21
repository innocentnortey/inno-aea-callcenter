import { SCREENS, type ScreenId } from "@/routes";
import type { Scenario, ScreenScenarios } from "./types";
import { screenScenarios as shared } from "./shared";
import { screenScenarios as scr01core } from "./scr01-core";
import { screenScenarios as scr01cards } from "./scr01-cards";
import { screenScenarios as scr02 } from "./scr02";
import { screenScenarios as scr03 } from "./scr03";
import { screenScenarios as scr04 } from "./scr04";
import { screenScenarios as scr05 } from "./scr05";
import { screenScenarios as scr06 } from "./scr06";
import { screenScenarios as scr07 } from "./scr07";
import { screenScenarios as scr08 } from "./scr08";
import { screenScenarios as scr09 } from "./scr09";
import { screenScenarios as scr10 } from "./scr10";
import { screenScenarios as scr11 } from "./scr11";
import { screenScenarios as scr12 } from "./scr12";

export interface ScenarioFile { slug: string; group: "shared" | "G1" | "G2" | "G3" | "G4" | "G5"; screens: ScreenId[]; screenScenarios: ScreenScenarios }
export const SCENARIO_FILES: ScenarioFile[] = [
  { slug: "shared", group: "shared", screens: [], screenScenarios: shared },
  { slug: "scr01-core", group: "G1", screens: ["SCR-1"], screenScenarios: scr01core },
  { slug: "scr01-cards", group: "G2", screens: ["SCR-1"], screenScenarios: scr01cards },
  { slug: "scr02", group: "G3", screens: ["SCR-2"], screenScenarios: scr02 },
  { slug: "scr03", group: "G3", screens: ["SCR-3"], screenScenarios: scr03 },
  { slug: "scr04", group: "G3", screens: ["SCR-4"], screenScenarios: scr04 },
  { slug: "scr05", group: "G4", screens: ["SCR-5"], screenScenarios: scr05 },
  { slug: "scr06", group: "G4", screens: ["SCR-6"], screenScenarios: scr06 },
  { slug: "scr07", group: "G5", screens: ["SCR-7"], screenScenarios: scr07 },
  { slug: "scr08", group: "G5", screens: ["SCR-8"], screenScenarios: scr08 },
  { slug: "scr09", group: "G5", screens: ["SCR-9"], screenScenarios: scr09 },
  { slug: "scr10", group: "G5", screens: ["SCR-10"], screenScenarios: scr10 },
  { slug: "scr11", group: "G5", screens: ["SCR-11"], screenScenarios: scr11 },
  { slug: "scr12", group: "G3", screens: ["SCR-12"], screenScenarios: scr12 },
];
export function allScenarios(): Scenario[] { return SCENARIO_FILES.flatMap((f) => f.screenScenarios.scenarios); }
export function scenariosFor(screen: ScreenId): Scenario[] { return allScenarios().filter((s) => s.screen === screen); }
export function sharedScenarios(): Scenario[] { return allScenarios().filter((s) => s.screen === "*"); }
export function isComplete(slug: string): boolean { return SCENARIO_FILES.find((f) => f.slug === slug)?.screenScenarios.complete === true; }
export function screenForPath(pathname: string): ScreenId | null {
  for (const s of SCREENS) {
    const re = new RegExp("^" + s.path.replace(/:[^/]+/g, "[^/]+") + "/?$");
    if (re.test(pathname)) return s.id;
  }
  return null;
}
