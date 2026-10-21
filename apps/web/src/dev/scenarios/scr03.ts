import type { ScreenScenarios } from "./types";

const OFF = { example: "OFF" };
const ON = { example: "ON" };
const WAITING = { example: "TURNED_OFF_WITH_WAITING" };
const R = "/demo";

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    { id: "scr03.default", screen: "SCR-3", state: "default", label: "Nobody online", route: R, ops: { getStaffing: OFF } },
    {
      id: "scr03.default-on", screen: "SCR-3", state: "default", flowState: "simulation on / off (FLOW-8)", label: "Simulation on", route: R, staffing: "simulated_on_shift",
      ops: { getStaffing: ON, setStaffing: WAITING }, notes: "The switch starts on.",
    },
    { id: "scr03.loading", screen: "SCR-3", state: "loading", label: "Checking staffing", route: R, ops: { getStaffing: { hang: true } }, notes: "'Checking...', switch disabled, static regions visible." },
    { id: "scr03.error-read", screen: "SCR-3", state: "error", label: "Staffing read fails", route: R, ops: { getStaffing: { fail: "network" } }, notes: "Retry link." },
    { id: "scr03.error-staffing-write", screen: "SCR-3", state: "error", label: "Staffing write fails", route: R, ops: { getStaffing: OFF, setStaffing: { fail: "network" } }, notes: "Flip the switch: it returns to off with the error line." },
    { id: "scr03.error-reset", screen: "SCR-3", state: "error", label: "Reset fails", route: R, ops: { resetDemo: { example: "RESET_FAILED" } }, notes: "500." },
    { id: "scr03.error-reset-in-progress", screen: "SCR-3", state: "error", label: "Reset already running", route: R, ops: { resetDemo: { example: "RESET_IN_PROGRESS" } }, notes: "409: the button reads Resetting... for a few seconds." },
    {
      id: "scr03.stale-staffing-changed", screen: "SCR-3", state: "stale", label: "Staffing changed elsewhere", route: R,
      ops: { getStaffing: { sequence: [OFF, OFF, OFF, OFF, OFF, ON] } },
      notes: "Within about 20 s: 'Staffing changed since you opened this page.' and the switch moves. Quicker: in the panel's per-operation select set getStaffing to ON.",
    },
    { id: "scr03.success-on", screen: "SCR-3", state: "success", flowState: "simulation on / off (FLOW-8)", label: "Turn simulation on", route: R, ops: { getStaffing: OFF, setStaffing: { example: "TURNED_ON" } } },
    {
      id: "scr03.success-off-waiting", screen: "SCR-3", state: "success", flowState: "shift ended with live-queued customers", label: "Turn off with 1 waiting", route: R, staffing: "simulated_on_shift",
      ops: { getStaffing: ON, setStaffing: WAITING }, notes: "Turn the switch off: the 1 waiting customer line.",
    },
    {
      id: "scr03.success-off-none", screen: "SCR-3", state: "success", label: "Turn off with nobody waiting", route: R, staffing: "simulated_on_shift",
      ops: { getStaffing: ON, setStaffing: { ...WAITING, transform: (b: Record<string, unknown>) => ({ ...b, converted_cases: 0 }) } },
      notes: "The 0-customers line (valid against StaffingResponse).",
    },
    {
      id: "scr03.success-reset", screen: "SCR-3", state: "success", flowState: "reset during a live chat (FLOW-12)", label: "Reset as Representative", route: R, role: "representative",
      ops: { resetDemo: { example: "RESET" } }, notes: "Reset: the line includes 'Open chats have ended.' and the role-reset sentence; the header role returns to Customer.",
    },
    {
      id: "scr03.success-reset-quiet", screen: "SCR-3", state: "success", label: "Reset with no open chats", route: R,
      ops: { resetDemo: { example: "RESET", transform: (b: Record<string, unknown>) => ({ ...b, open_chats_ended: 0, roles_reset: 0 }) } }, notes: "No chats sentence.",
    },
    { id: "scr03.disabled-saving", screen: "SCR-3", state: "disabled", label: "Switch saving", route: R, ops: { getStaffing: OFF, setStaffing: { hang: true } }, notes: "Flip the switch: it stays disabled while saving." },
    { id: "scr03.disabled-resetting", screen: "SCR-3", state: "disabled", label: "Reset running", route: R, ops: { resetDemo: { hang: true } }, notes: "Confirm a reset: the button reads 'Resetting...' and stays disabled." },
  ],
};
