// ESLint for apps/web. Generated and build output is ignored.
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";

export default tseslint.config(
  { ignores: ["dist/", "node_modules/", "test-results/", "playwright-report/", ".tmp/", "src/api/types.gen.ts"] },
  {
    files: ["**/*.{ts,tsx,js,mjs}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { ecmaVersion: 2022, globals: { ...globals.browser, ...globals.node } },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-hooks/exhaustive-deps": "warn",
      "@typescript-eslint/no-unused-expressions": ["error", { allowShortCircuit: true, allowTernary: true }],
      "@typescript-eslint/no-unused-vars": ["error", { caughtErrors: "none", argsIgnorePattern: "^_" }],
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/dev/**", "src/main.tsx", "src/**/*.test.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [{ group: ["**/dev/**", "@/dev/**"], message: "The dev-only layer is imported only by src/main.tsx" }] }],
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/api/transport.ts", "src/dev/**", "src/**/*.test.{ts,tsx}"],
    rules: { "no-restricted-globals": ["error", { name: "fetch", message: "Use callOp / useOp / useAction" }] },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/dev/**", "src/**/*.test.{ts,tsx}"],
    rules: {
      "no-restricted-syntax": ["error", { selector: 'MemberExpression[object.name="document"][property.name="cookie"]', message: "Cookies are set by the server; the dev layer fakes it" }],
    },
  },
);
