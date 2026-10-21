"""Parse the three UX-1 Markdown sources for gen_ux1.py, and guard against drift.

What is read from the Markdown at every build (so it can't go stale):
  journeys, flow metadata (stories, hard problem, start, end), each flow's contracts (step table),
  the requirement coverage table, the story list, the screen table, the error-branch table and the
  draft-contract table.
What stays hand-maintained in gen_ux1.py (and is therefore checked or snapshotted here):
  * the hand-drawn flowcharts: check_flow() compares every node label, edge and edge label with the
    flow's Mermaid and fails the build on any difference;
  * the sitemap and summary diagrams, the "why" paragraphs, the numbered text equivalents and all
    prose: these cannot be checked mechanically. snapshot_guard() therefore keeps a copy of each
    source as it was at the last accepted build; when a source changes it prints the diff and stops,
    so a person reads the diff, updates the hand-written parts, and re-runs with --accept-changes.
"""
import difflib
import re
import shutil
import sys
from pathlib import Path

NORM = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def norm(s):
    return re.sub(r"\s+", " ", s.translate(NORM)).strip()


def strip_md(s):
    return s.replace("`", "").replace("**", "").strip()


def table_rows(lines):
    out = []
    for ln in lines:
        if ln.startswith("|") and not re.match(r"^\|\s*-", ln):
            out.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return out[1:] if out else out  # drop header


def section(text, start_pat, end_pat=r"^## "):
    m = re.search(start_pat, text, re.M)
    if not m:
        raise SystemExit(f"source parse: section {start_pat!r} not found")
    rest = text[m.end():]
    e = re.search(end_pat, rest, re.M)
    return rest[: e.start()] if e else rest


# ---------------------------------------------------------------- USER_FLOWS.md
def parse_flows(text):
    flows = {}
    for m in re.finditer(r"^### (FLOW-\d+) · (.+)$", text, re.M):
        fid = m.group(1)
        body = text[m.end():]
        nxt = re.search(r"^(### |## |---)", body, re.M)
        body = body[: nxt.start()] if nxt else body
        meta = {}
        for key, pat in (("stories", r"^- Stories: (.+)$"), ("hp", r"^- Hard problem: (.+)$")):
            mm = re.search(pat, body, re.M)
            meta[key] = mm.group(1).strip()
        se = re.search(r"^- Start: (.+?) · End: (.+)$", body, re.M)
        meta["start"], meta["end"] = se.group(1).strip(), se.group(2).strip()
        mer = re.search(r"```mermaid\n(.*?)```", body, re.S).group(1)
        meta["mermaid"] = mer
        rows = table_rows(body[body.index("```", body.index("```mermaid") + 3) + 3:].splitlines())
        cons = []
        for r in rows:
            for c in re.findall(r"CON-\d+", r[4]):
                if c not in cons:
                    cons.append(c)
        meta["cons"], meta["title"] = cons, m.group(2).strip()
        flows[fid] = meta
    return flows


def parse_journeys(text):
    out = []
    for blk in re.findall(r"```mermaid\njourney\n(.*?)```", text, re.S):
        title, secs = None, []
        for ln in blk.splitlines():
            s = ln.strip()
            if s.startswith("title "):
                title = s[6:].strip()
            elif s.startswith("section "):
                secs.append((s[8:].strip(), []))
            elif s:
                step, score, actors = [p.strip() for p in s.rsplit(":", 2)]
                secs[-1][1].append((step, int(score), actors))
        out.append((title, secs))
    return out


def parse_errors(text):
    return [(r[0], r[1]) for r in table_rows(section(text, r"^## Error branches covered").splitlines())]


def parse_cons(text):
    rows = table_rows(section(text, r"^## Draft contracts").splitlines())
    return [(r[0], strip_md(r[1]), r[2], r[3]) for r in rows]


def mermaid_graph(mer):
    """Node labels and (from-label, to-label, edge-label) triples of a Mermaid flowchart."""
    labels = {}
    for m in re.finditer(r"\b(\w+)\s*(\[|\{)(.+?)(\]|\})", mer):
        labels[m.group(1)] = norm(m.group(3))
    edges = []
    for ln in mer.splitlines():
        m = re.match(r"^\s*(\w+)(?:\s*[\[\{].*?[\]\}])?\s*(?:--\s*(.+?)\s*-->|-->)\s*(\w+)", ln)
        if m:
            edges.append((m.group(1), norm(m.group(2) or ""), m.group(3)))
    return labels, [(labels.get(a, a), l, labels.get(b, b)) for a, l, b in edges]


def check_flow(fid, mer, nodes, edges):
    """Fail loudly if a hand-drawn flow differs from its Mermaid source."""
    labels, medges = mermaid_graph(mer)
    mine_labels = sorted(norm(n["t"]) for n in nodes.values())
    src_labels = sorted(labels.values())
    mine_edges = sorted((norm(nodes[e["a"]]["t"]), norm(e.get("l", "")), norm(nodes[e["b"]]["t"])) for e in edges)
    problems = []
    for lab in sorted(set(src_labels) - set(mine_labels)):
        problems.append(f"  node in source, not on page: {lab}")
    for lab in sorted(set(mine_labels) - set(src_labels)):
        problems.append(f"  node on page, not in source: {lab}")
    for e in sorted(set(medges) - set(mine_edges)):
        problems.append(f"  edge in source, not on page: {e}")
    for e in sorted(set(mine_edges) - set(medges)):
        problems.append(f"  edge on page, not in source: {e}")
    return [f"{fid} diagram differs from USER_FLOWS.md:"] + problems if problems else []


# ---------------------------------------------------------------- USER_STORIES.md
USERS = {"homeowner": "Homeowner", "representative": "Representative", "supervisor": "Supervisor",
         "business owner": "Business owner", "reviewer": "Reviewer"}


def parse_stories(text):
    out, user = [], None
    for ln in text.splitlines():
        m = re.match(r"^## Stories — (.+?)(?: \(|$)", ln)
        if m:
            user = USERS[m.group(1).strip()]
            continue
        m = re.match(r"^### (US-\d+) · (.+)$", ln)
        if m:
            out.append({"id": m.group(1), "user": user, "title": m.group(2).strip()})
            continue
        if out:
            m = re.match(r"^- Priority: (P\d)", ln)
            if m:
                out[-1]["pri"] = m.group(1)
            m = re.search(r"Hard problem: (.+)$", ln)
            if m and ln.startswith("- Evidence"):
                out[-1]["hp"] = m.group(1).strip()
    return out


def parse_coverage(text):
    rows = table_rows(section(text, r"^## Requirement coverage").splitlines())
    return [(r[0], r[1]) for r in rows]


# ---------------------------------------------------------------- SITEMAP.md
def parse_screens(text):
    rows = table_rows(section(text, r"^## Screens").splitlines())
    out = []
    for sid, surf, reach, flows, notes in rows:
        cm = re.search(r"\s*Contracts: (.+)$", notes)
        cons = [int(x) for x in re.findall(r"CON-(\d+)", cm.group(1))] if cm else []
        notes_txt = notes[: cm.start()].strip() if cm else notes
        out.append((sid, strip_md(surf), strip_md(reach), [int(x) for x in re.findall(r"FLOW-(\d+)", flows)],
                    cons, strip_md(notes_txt)))
    return out


def parse_sitemap_header(text):
    m = re.search(r"^> \*\*(Three surfaces[^*]+)\*\*", text, re.M)
    return m.group(1) if m else None


# ---------------------------------------------------------------- snapshot guard
def snapshot_guard(root, sources, snapdir, accept):
    snapdir.mkdir(exist_ok=True)
    changed = []
    for s in sources:
        cur = (root / s).read_text()
        snap = snapdir / Path(s).name
        if snap.exists() and snap.read_text() != cur:
            changed.append(s)
            sys.stderr.write("".join(difflib.unified_diff(
                snap.read_text().splitlines(True), cur.splitlines(True), f"last-built/{Path(s).name}", s)))
    if changed and not accept:
        raise SystemExit(
            f"\nSOURCES CHANGED since the last accepted build: {', '.join(changed)}.\n"
            "The page's prose, text equivalents and the sitemap/summary diagrams are hand-maintained.\n"
            "Read the diff above, update gen_ux1.py where it is affected, then re-run with --accept-changes.\n"
            "Never just re-stamp the hashes.")


def accept_snapshots(root, sources, snapdir):
    snapdir.mkdir(exist_ok=True)
    for s in sources:
        shutil.copyfile(root / s, snapdir / Path(s).name)
