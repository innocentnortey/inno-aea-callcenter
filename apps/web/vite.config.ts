/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";
export default defineConfig(({ mode }) => {
  const mock = mode === "mock";
  const target = mock ? `http://127.0.0.1:${process.env.MOCK_PORT ?? "4019"}` : `http://127.0.0.1:${process.env.API_PORT ?? "8000"}`;
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: { proxy: { "/api": { target, changeOrigin: true } } },
    test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], include: ["src/**/*.test.{ts,tsx}"], restoreMocks: true },
  };
});
