> **Provenance:** copy of `Gauntlet AI/.claude/rules/gauntlet-hosting-default.md` (zero-to-hero principles pack), copied 2026-10-14. Change the original first, then re-copy.

# Railway Is the Default Host for Gauntlet Projects

Project-wide. Recorded 2026-10-10 at Innocent's instruction ("we're already using Railway; that
should be a default for all Gauntlet projects").

**The rule.** When a Gauntlet project (weekly build or hiring-partner project) needs a deployed
runtime, deploy it on **Railway** under Innocent's existing plan, as another service or project.
Don't open a hosting decision from scratch, and don't reach for Vercel, Netlify or Render by
default. Neon stays the default Postgres (free tier) unless a project's brief says otherwise, or the
project owner chooses Railway's own Postgres to keep the whole deployment in one place (Cerbo did,
2026-10-10, PRD §13 R-DB).

**Why.**
- Railway is already paid for and known: Equinox runs there (PRD 0.5 R-RUNENV), and Cerbo moved
  there on 2026-10-10 (PRD §13 R-HOST).
- A long-running Node/Python process avoids the serverless pitfalls that bit the Cerbo design
  review: per-request cold starts, no persistent database pool, 1-hour log retention on Vercel
  Hobby, and Vercel's Hobby fair-use clause ("non-commercial personal use only"; "processing
  payment from visitors" counts as commercial), which a payments-shaped demo trips.
- One operator, one dashboard, one billing line.

**Facts to cite (railway.com/pricing and docs.railway.com/guides/logs, read 2026-10-10):** Hobby is
$5/month and includes $5 of usage (memory ≈ $10/GB-month held, CPU ≈ $20/vCPU-month used, egress
$0.05/GB); usage above $5 bills in full. Free plan: $1/month credit, 1 vCPU / 0.5 GB, 1 project,
3-day logs, no custom domains. Trial: one-time $5 credit for 30 days. Logs: 7-day retention on
Hobby, structured JSON with queryable attributes, 500 lines/s per replica. Stopped services cost
nothing. No commercial-use restriction on the page.

**How to apply.**
- In a project's PRD or decision record, the hosting decision reads "Railway (Gauntlet default,
  `Gauntlet AI/.claude/rules/gauntlet-hosting-default.md`)" plus any project-specific reason.
- Spend ceilings for a project count Railway as **$0 incremental** on the existing plan unless the
  project needs its own paid project; say which.
- Secrets are Railway variables, never committed. Migrations run from the Railway service or a
  one-off job, against Neon's direct (non-pooled) endpoint.
- If a brief *requires* another host, the brief wins; record the exception.
