# Decisions for Innocent from the UX ↔ backend join

**Date:** 2026-10-21. **Format:** story, options, decision (`decision-requests-story-driven`). Six choices only you can make:
what goes in the signed contracts, what a reviewer sees, and what gets committed. Each is one line to answer. Engineering
choices the audits raised are made in [`backend-amendments.md`](backend-amendments.md) and listed at the end, so you can
overrule any of them.

Background in one paragraph: three audits compared the frontend the UX session built (`apps/web`) with what the backend
tickets will actually send. They found 94 mismatches, 18 of them serious ([`README.md`](README.md) has the full list and who
fixes each). Most are fixes for one side or the other. These six are not.

---

## 1. WEB-1 · Which files may load before the demo login

**The story.** The login screen (SCR-12) is part of the React app. To draw it, the browser must first download the app's
built script and style files (names like `/assets/index-3f9a.js`) and its fonts. Your rule R-48 says one login gates the whole
site, and SCREEN_SPECS SCR-12 says `/login` and `/healthz` are the only routes that answer without a session. Read literally,
`/login` would answer but its own files would be refused, so the reviewer sees a blank page and can never sign in. This was
asked as WEB-1 in the 7b ledger (`docs/plans/7b-decisions/web.md`, lines 23–47) and is still open.

**What the audit adds.** The customer audit (C-1) checked the built app: its `index.html` needs `/assets/index-*.js`,
`/assets/*.css` and lazy-loaded chunks before anyone is signed in. **Option A works with the app exactly as built. Option B
needs a separate, self-contained login page that does not exist today**: the UX session would have to build it as part of
UX-4 (styles and script inlined) and keep it matching SCR-12's design and copy from then on. AEA-49 (which serves the app) and
AEA-58/AEA-62 (the browser journeys) are written for A; B or C changes their public-path checks (amendment AEA-49-2).

**Option A: `/login` plus the built files under `/assets/` and `/fonts/` are public; every other page and every `/api` call
needs the login (recommended).** No extra work. R-48 gains "plus the login page's static files". Those files hold no data and
are already public in the repo (R-42). AEA-49 gets the `risk::security` label.
**Option B: a self-contained login page at `/login`, nothing else public.** Keeps R-48's letter. About half a day for the UX
session before UX-4 sign-off, which is on the build's critical path from wave 3, and a second login screen to keep in step.
**Option C: the whole app shell is public; only `/api` is gated, and the app sends itself to `/login` after a 401.** Simplest
server. A stranger briefly sees the empty frame of the staff screens, and the server-side redirect moves into the browser.

*Recommended: A.* It works today, makes nothing with data public, and the deviation from R-48 is limited to files already in
the public repo.

> **Decision needed:** Which files may load without the demo login: `/login` plus its built asset files (A), a separate
> self-contained login page only (B), or the whole app shell (C)?

---

## 2. Add `CaseDetail.events.last_event_id` to the signed OpenAPI?

**The story.** A representative opens a case (SCR-6). The page loads the case as a snapshot (CON-12 `getCase`), then opens the
case's live event stream (CON-21) to hear about new customer messages and changes. The snapshot doesn't say which events it
already includes, so the server replays the case's events from the start on top of it. If the case's chat closed earlier, that
old `chat_closed` event re-applies and the page opens saying "This chat is no longer live." with a disabled reply box, even
when it is live again. The customer chat already avoids this: its start response carries `events.last_event_id` (CON-1), and
the stream resumes from there. The case view has no twin (staff audit B5).

**Why it is yours.** The fix is a field in the signed OpenAPI, and the checklist's *Skips* row says a contract change "reopens
UX-3 and breaks UX-4's pinned types". Concretely: the UX session regenerates its types and contract index, the backend's
drift check (AEA-59) follows, and AEA-29 and AEA-45 each gain one criterion (AEA-29-5, AEA-45-2). The field is additive and can
be optional, so no existing example becomes invalid.

**Option A: add `events: {last_event_id}` to `CaseDetail`, as CON-1 already has (recommended).** The page connects with it as
`Last-Event-ID` and replays nothing it already shows. About an hour on each side; a new contract version.
**Option B: keep the contract; the page ignores replayed events dated at or before the snapshot.** No contract change. But the
demo clock only moves when someone advances it, so a whole demo session usually shares one demo time: old and new events then
carry the **same** time, and the filter either drops new events or keeps old ones. It works only by luck.
**Option C: the server starts a case stream with no `Last-Event-ID` at the newest event.** No contract change, but any event
written between the snapshot and the connect is lost, which breaks the stream's no-loss rule.

*Recommended: A.* It is the same mechanism the chat already uses, and B fails in the normal case, not the edge case.

> **Decision needed:** Should the signed OpenAPI gain `CaseDetail.events.last_event_id` (A), or stay as it is with the
> page filtering replayed events (B)?

---

## 3. Commit the working tree now?

**The story.** The build runs each ticket in its own git worktree, cut from `main`. Today `main` holds one commit, the Project 1
snapshot (`ed4ca89`). Everything since is untracked: not only `apps/` and `docs/ux/` (the shell audit's finding F1) but
`docs/design/` (the contracts), `docs/plans/` (the slice plan and all 62 ticket files), `src/`, `pyproject.toml`, `uv.lock`
and most of the project's `.claude/` rules. A worktree cut from `main` today would have none of it: AEA-01 could not find its
`pyproject.toml`, AEA-23's response check could not find the OpenAPI, and AEA-59's drift check could not find `apps/web`.
Commits need your yes (project rule).

**What a commit would include.** `.gitignore` already keeps `.env`, `var/` (67 MB of local runtime) and `.venv/` out, and
`apps/web/.gitignore` keeps `node_modules/`, `dist/` and test output out. So no secret and no build output would be tracked.
Pushing is a separate yes: GitLab's `main` starts with your README commit, so the first push builds on it with no force push,
and the project is public (R-42).

**Option A: commit the whole tree to local `main` now, before wave 0 is dispatched (recommended).** One commit after a last
`git status` check; the UX session pauses at a stable point first and commits its later work itself, with your yes. Every
worktree then sees the contracts, the tickets and the frontend.
**Option B: commit the backend side now, `apps/` and `docs/ux/` at UX-4 sign-off.** Keeps unfinished UX work out of history.
But AEA-23 (wave 1) needs at least `docs/ux/03-structure/ui-contracts.openapi.yaml`, and AEA-59 (wave 2) needs `apps/web`, so
this splits `docs/ux/` and makes wave 2 wait for UX-4.
**Option C: don't commit; copy the files into each worktree.** Nothing in history yet, but every ticket branch would merge
without the files it was built against. Fragile; not recommended.

*Recommended: A.* Nothing in the build can start correctly without it, and git history is where an unfinished UX state is
safest.

> **Decision needed:** May the whole working tree, `apps/` and `docs/ux/` included, be committed to local `main` now, before
> wave 0 starts (A), or should `apps/` and `docs/ux/` wait for UX-4 sign-off (B)?

---

## 4. Should the chat stream document a 410 for an ended chat?

**The story.** When a chat has ended (a demo reset, or a representative closed it), the backend's shared ownership check answers
**410 `SESSION_ENDED`** for that thread on every chat route. The chat's event stream (CON-3, ticket AEA-41) uses the same check.
But the signed OpenAPI documents only 401 and 404 for the stream, and the backend's one response checker fails any status the
OpenAPI does not list (customer audit D-2). AEA-41 already carries this as its needs-decision ND-1, recommending that the
stream answer 404 instead. On the frontend, the stream today stops silently on both 404 and 410, and the chat keeps looking open
until the next send; the UX session fixes that either way (the stream reports "ended", and the page re-reads the thread, which
does answer 410 with the reason).

**Option A: keep the contract; the stream answers 404 for an ended thread (recommended).** No contract change; AEA-41 stays as
written. The page learns *why* the chat ended from its next thread read, which already returns 410 with `reason`.
**Option B: add 410 to `streamChatEvents` in the OpenAPI.** The stream itself says the chat ended and why. A contract change
(reopens UX-3, types regenerated); AEA-41's AC-7 is replaced (amendment AEA-41-2).

*Recommended: A.* The reason is already one call away, and it avoids a contract change for a state the page handles the same
way.

> **Decision needed:** Should the chat stream keep answering 404 for an ended chat (A), or should the OpenAPI gain a 410 for it
> (B)?

---

## 5. What a reviewer sees when the login is rate limited

**The story.** After 10 wrong logins from one IP address in 10 minutes, the server refuses every login from that address for a
while, the right one included, with `429 LOGIN_RATE_LIMITED`. Two signed UX-3 documents disagree on what the screen then says.
SCREEN_SPECS N-28: "a throttle that answers the same sentence" as a wrong password ("That username or password didn't work.
Check the README and try again."). UI_CONTRACTS CON-22's error table: "Too many attempts. Wait a moment and try again."
The frontend follows N-28 today, and AEA-58 AC-6 tests exactly that. The customer audit (C-3) points out the effect: a reviewer
who types the **correct** README values during a throttle is told they are wrong. Reviewers in one office share one IP, so a
colleague's typos can cause it.

**Option A: keep N-28, one sentence for every refusal.** Reveals nothing about throttling. No change anywhere. Confusing in
exactly the case above.
**Option B: a separate line for the throttle, using UI_CONTRACTS' wording and the wait time the server sends (recommended).**
For example "Too many tries from here. Try again in 40 seconds." It says nothing about which field was wrong, so it gives an
attacker nothing new. One copy change in `apps/web`, the N-28 line corrected through the UX track, AEA-58 AC-6 replaced
(amendment AEA-58-3). No OpenAPI change: the code already exists.

*Recommended: B.* Telling a reviewer their correct password is wrong is the worse failure, and the throttle message leaks nothing.

> **Decision needed:** During a login throttle, should SCR-12 show the same sentence as a wrong password (A), or its own
> "too many tries, wait N seconds" line (B)?

---

## 6. Does a chat resume after signing in again?

**The story.** A reviewer is chatting when their demo session ends (it lasts 12 hours) or they sign out. They sign in again in
the same tab. SCREEN_SPECS SCR-1 says "After sign-in the reviewer returns here and the chat resumes if it is still open". The
backend does something else: every sign-in creates a new login session, and a thread belongs to the session that started it, so
the earlier thread answers **404** to the new session (`stage7/web.md` §2 and §4, `owned_thread`). The page then clears the old
thread and starts a new chat. The AEA-58 writer found this; AEA-62 currently asserts neither behaviour and waits for you. Anything
the old chat escalated stays visible to staff either way.

**Option A: start fresh after a new sign-in (recommended).** No backend change. The UX session corrects the SCR-1 line (for
example "After sign-in, a new chat starts.") through the UX track; AEA-58 and AEA-62 then assert it (amendments AEA-58-4,
AEA-62-3).
**Option B: resume, when the tab still holds the thread id, the thread is still open and its old session no longer exists.**
Matches SCR-1 as written. But it turns a thread id into a key that takes over an orphaned chat, and thread ids are written into
the server's request logs as correlation ids, so anyone who can read the logs could adopt a chat. It changes the shared
ownership check (web.md §4) and three tickets' criteria (AEA-40, 41, 42), needs a security review, and costs about half a day.
(Resuming by the login itself is not an option: everyone shares one demo login.)

*Recommended: A.* A new sign-in is a natural fresh start for a demo, and B weakens the one check that keeps reviewers' chats
apart.

> **Decision needed:** After signing in again, should SCR-1 start a new chat (A) or resume the earlier one when the tab still
> has it (B)?

---

## Not asked: settled as engineering, or no contract change recommended

You can overrule any of these; none needs an answer for the build to continue.

| Item | What we did | Source |
|---|---|---|
| DAT-3: does the README hold the demo login? | Already logged with you (also slice plan Q-4); SCR-12's copy follows your answer (customer C-4) | `7b-decisions/data.md` |
| A unit enum (`count`, `ms`, `share`) in the OpenAPI | Not proposed. AEA-53 and AEA-48 fix the vocabulary on the server side (AEA-53-1, AEA-48-1); the OpenAPI keeps a free string | shell A1 |
| `limits` in `ChatThread`; a retry time in the `RATE_LIMITED` notice | Not proposed; the page caches limits and guesses 60 s, both harmless today | customer A-8, D-4 |
| Example timestamps with a space (`2026-10-16 14:31:00-05:00`); `date_label` in staff.md but not the OpenAPI | Recorded by AEA-08; the route returns the OpenAPI's keys (AEA-47-1) | staff A5, A7 |
| The customer called "You" in staff-side examples | Staff reads send `display_name: null`; the page shows "Customer" | staff A3 |
| Live chat actions bumping the case version | They don't (staff.md §5); AEA-52 AC-4 corrected | staff A4 |
| Who marks old cards `answered` after a reload | AEA-40 (the backend), with a frontend fallback if storage can't give it | customer A-3 |
| How the deploy image builds the frontend | It copies the signed OpenAPI next to `apps/web` and runs the UX recipe unchanged | shell F2 |
