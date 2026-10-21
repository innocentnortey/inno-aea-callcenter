# apps/web: the Meridian front end

React 19 + Vite + TypeScript + Tailwind v4 + hand-written shadcn-style components over Radix + lucide-react.
It is the real front end (UX-4 prototype = the real thing); in mock mode it runs against a Prism mock of the OpenAPI file.
Foundation slice of the UX-4 fan-out: shell, router, tokens, API client, dev layer, state switcher. Screens are stubs until their groups land.

## Run

Two terminals, from `apps/web/`:

```
npm run mock        # Prism on http://127.0.0.1:4019 (the OpenAPI file's servers entry)
npm run dev:mock    # Vite on http://127.0.0.1:5184, proxies /api to Prism, mounts the dev layer
```

`npm run dev` proxies `/api` to the real backend (`API_PORT`, default 8000, not built yet) and has no dev layer.
From a laptop: `ssh -L 5184:127.0.0.1:5184 claude-vultr`, then open http://127.0.0.1:5184.

Env vars: `WEB_PORT` (5184), `MOCK_PORT` (4019), `API_PORT` (8000). Ports 4010/5173, 4012/5180, 4013/5183 belong to other projects.

## Mock-mode URL parameters (read once at start; the URL is rewritten to reproduce the state)

`?signedin=0|1` `?role=customer|representative|supervisor|owner` `?staffing=on|off` `?ex=getQueue:SEEDED,applyCaseAction:409/NOT_ALLOWED_IN_STATE`
`?delay=1500|4000|hang` `?theme=light|dark` `?scenario=<id>`. The component kit is at `/__kit?signedin=1`.

## Scripts

`typecheck`, `lint`, `test`, `build`, `check:dist` (no dev layer in `dist/`), `gen:types`, `examples`, `check:gen`, `smoke:mock` (every operation x every named example against Prism), `test:e2e` (Playwright, 12 routes x 2 widths, axe).
Run Playwright under a cap: `perl -e 'alarm 300; exec @ARGV' npx playwright test`; it starts and stops its own Prism and Vite, so run it with ports 4019 and 5184 free.

## Do not hand-edit

`src/api/types.gen.ts` and `src/api/contract.gen.json` are generated from `docs/ux/03-structure/ui-contracts.openapi.yaml` and committed; the `pre*` scripts regenerate them and `check:gen` fails when they are stale. Never edit the OpenAPI file from here: a gap is a request to its owners.

## Where things live

`src/api` (typed client, SSE, hooks) · `src/state` (session, demo status, theme) · `src/components/{ui,shared,shell}` · `src/screens/scrNN` (one folder per screen; `scr01/contract.ts` and `blocks.tsx` are frozen seams between the chat groups) · `src/dev` (mock-only: scenarios, reactions, scripted streams, panel, kit; imported only by `src/main.tsx`) · `src/styles` (tokens: the only place hex values live).

## Resolved versions (2026-10-21)

react 19.3.1, react-router 7.18.4, vite 6.4.5, tailwindcss 4.3.3, typescript 5.8.3, lucide-react 1.60.0, @playwright/test 1.64.1, @fontsource/inter 5.3.0, @fontsource/instrument-sans 5.3.0, @fontsource/geist-mono 5.3.0, yaml 2.9.1, class-variance-authority 0.7.1, clsx 2.1.1, tailwind-merge 3.7.0, @radix-ui/react-radio-group 1.5.1. Pinned exactly: openapi-typescript 7.13.0, @stoplight/prism-cli 5.15.11, vitest 3.2.7, jsdom 26.1.0, @testing-library/react 16.3.3, eslint 9.39.5.
No dependency was added beyond the plan's list.
