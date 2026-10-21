import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/index.css";
import { applyTheme } from "./state/theme";
import App from "./App";

function start() {
  applyTheme();
  createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
}
// Mock mode only (`npm run dev:mock`). Vite replaces import.meta.env.MODE at build time, so a production build drops this
// branch and src/dev/ entirely (checked by scripts/check-dist.mjs).
if (import.meta.env.MODE === "mock") void import("./dev/install").then((m) => m.installDev()).then(start);
else start();
