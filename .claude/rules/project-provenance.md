# Project Provenance — Remote and Host Policy

> **Provenance:** short policy form of `Gauntlet AI/.claude/rules/gauntlet-gitlab-versioning.md`,
> as that file's 2026-09-19 note recommends for spin-off repos. Mechanics and SSH troubleshooting
> stay in the original. Created 2026-10-14; repo renamed 2026-10-20.

- **Name:** `inno-aea-callcenter` (renamed from `inno-aea-onboarding` on 2026-10-20 with
  Innocent's approval, before any remote existed). First commit `ed4ca89` and tag
  `project-1-onboarding-snapshot` hold the pre-pivot tree.
- **`origin` is Gauntlet's GitLab:** `git@labs.gauntletai.com:innocentnortey/inno-aea-callcenter.git`
  (SSH port 22022). Innocent creates the GitLab project; Claude does not. **Created by Innocent 2026-10-21:** project id 2318, public (R-42), `main` starts with his README commit (the first push builds on it; no force push). `origin` added locally 2026-10-21. Use `env -u GITLAB_TOKEN glab … --hostname labs.gauntletai.com` (the shell's `GITLAB_TOKEN` is stale).
- **No `upstream`.** This repo is greenfield, not a fork.
- **GitHub mirror only with Innocent's explicit yes.** The PDF asks for a "source repository"
  without naming GitHub; check the portal's submission form before assuming a mirror is needed.
- **Commit and push only when Innocent asks.**
- **Host:** Railway by default (`gauntlet-hosting-default.md`). The brief requires a public URL
  for an interactive web app; no other host is named.
