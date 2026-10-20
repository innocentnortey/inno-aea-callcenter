# Project Provenance — Remote and Host Policy

> **Provenance:** short policy form of `Gauntlet AI/.claude/rules/gauntlet-gitlab-versioning.md`,
> as that file's 2026-09-19 note recommends for spin-off repos. Mechanics and SSH troubleshooting
> stay in the original. Created 2026-10-14.

- **`origin` is Gauntlet's GitLab:** `git@labs.gauntletai.com:innocentnortey/inno-aea-onboarding.git`
  (SSH port 22022). Innocent creates the GitLab project; Claude does not. **Not created yet.**
- **No `upstream`.** This repo is greenfield, not a fork.
- **GitHub mirror only with Innocent's explicit yes.** The brief requires a GitHub repository for
  submission, so a mirror will probably be needed. It is not yet approved.
- **Commit and push only when Innocent asks.**
- **Host:** Railway by default (`gauntlet-hosting-default.md`). The brief names Supabase for
  Postgres + Auth; whether that overrides the Neon default is a PRD decision, not yet made.
