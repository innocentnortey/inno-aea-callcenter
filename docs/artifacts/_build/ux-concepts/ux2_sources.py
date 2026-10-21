"""Parse the three UX-2 Markdown sources for gen_ux2.py, and guard against drift.

Read from the Markdown at every build (so it can't go stale):
  * DESIGN-DIRECTIONS.md: each direction's feeling line, its anatomy table, its house-texture check items and
    result line, and its credited Dribbble references (title, designer, shot URL, local image);
  * REFERENCES.md: the reference -> product mapping table (all findings);
  * CONCEPTS.md: the comparison table and the "every customer flow, end to end" table.
HAND-MAINTAINED in gen_ux2.py: the story, the decision cards (D1-D3), the "findings that changed the flows" cards,
the review notes on the built screens, the alt texts and every other sentence. snapshot_guard() therefore keeps a
copy of each source as it was at the last accepted build; when a source changes it prints the diff and stops, so a
person reads the diff, updates the hand-written parts, and re-runs with --accept-changes.
"""
import difflib
import re
import shutil
import sys
from pathlib import Path


def strip_md(s):
    s = s.replace("`", "").replace("**", "")
    return re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"\1", s).strip()


def table_rows(lines):
    out = []
    for ln in lines:
        if ln.startswith("|") and not re.match(r"^\|\s*-", ln):
            out.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return out[1:] if out else out


def section(text, start_pat, end_pat=r"^## "):
    m = re.search(start_pat, text, re.M)
    if not m:
        raise SystemExit(f"source parse: section {start_pat!r} not found")
    rest = text[m.end():]
    e = re.search(end_pat, rest, re.M)
    return rest[: e.start()] if e else rest


# ---------------------------------------------------------------- DESIGN-DIRECTIONS.md
def parse_directions(text):
    out = {}
    for m in re.finditer(r"^## (A\d) · (.+?)(?: \(recommended\))?$", text, re.M):
        did = m.group(1)
        body = text[m.end():]
        nxt = re.search(r"^## ", body, re.M)
        body = body[: nxt.start()] if nxt else body
        d = {"name": m.group(2).strip(), "recommended": "(recommended)" in m.group(0)}
        d["feeling"] = re.search(r"^- \*\*Feeling:\*\* (.+)$", body, re.M).group(1).strip()
        d["anatomy"] = {strip_md(r[0]): (r[1], r[2]) for r in table_rows(section(body, r"^### Component anatomy", r"^- \*\*").splitlines())}
        checks = []
        joined = re.sub(r"\n[ ]{5,}(?=\S)", " ", body)  # wrapped continuation lines of a numbered item
        for cm in re.finditer(r"^[ \t]*(\d)\. (.+?): \*\*(no|watch|yes)\.?\*\*\.?[ \t]*(.*)$", joined, re.M):
            checks.append((int(cm.group(1)), cm.group(2).strip(), cm.group(3), cm.group(4).strip()))
        d["checks"] = checks
        d["result"] = re.search(r"\*\*Result: (.+?)\*\*", body).group(1).strip()
        refs = []
        for rm in re.finditer(r"^- \*\*(.+?)\*\* — (.+?) · (https://dribbble\.com/\S+) · `(references/[^`]+)`", body, re.M):
            refs.append({"title": rm.group(1), "designer": rm.group(2), "url": rm.group(3), "file": rm.group(4)})
        d["refs"] = refs
        d["also"] = re.findall(r"^- also cites (.+)$", body, re.M)
        out[did] = d
    return out


def parse_method(text):
    """The Dribbble numbers stated in the file's method line."""
    t = re.sub(r"\s*\n>\s*", " ", text)
    return {
        "searches": re.search(r"(\w+) searches:", t).group(1),
        "shots": re.search(r"\*\*(\d+) unique shots\*\*", t).group(1),
        "sheets": re.search(r"as (\d+) numbered contact sheets", t).group(1),
        "opened": re.search(r"(\d+) were opened at ([\d×]+)", t).group(1),
        "opened_at": re.search(r"(\d+) were opened at ([\d×]+)", t).group(2),
        "kept": re.search(r"\*\*(\d+) are kept\*\*", t).group(1),
    }


# ---------------------------------------------------------------- REFERENCES.md
def parse_findings(text):
    rows = table_rows(section(text, r"^## Reference → product mapping").splitlines())
    keys = ("id", "pattern", "source", "application", "maps", "why", "confidence", "kept")
    return [dict(zip(keys, [strip_md(c) for c in r])) for r in rows]


def parse_products(text):
    rows = table_rows(section(text, r"^## What was examined, and how").splitlines())
    return [(strip_md(r[0]).split(":")[0].split(" (")[0], r[2]) for r in rows]


# ---------------------------------------------------------------- CONCEPTS.md
def parse_comparison(text):
    rows = table_rows(section(text, r"^## Comparison", r"^## |\Z").splitlines())
    return [[strip_md(c) for c in r] for r in rows]


def parse_flow_table(text):
    rows = table_rows(section(text, r"^### Every customer flow, end to end", r"^---|^## ").splitlines())
    return [[strip_md(c) for c in r] for r in rows]


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
            "The story, decision cards, finding cards, review notes and alt texts are hand-maintained.\n"
            "Read the diff above, update gen_ux2.py where it is affected, then re-run with --accept-changes.\n"
            "Never just re-stamp the hashes.")


def accept_snapshots(root, sources, snapdir):
    snapdir.mkdir(exist_ok=True)
    for s in sources:
        shutil.copyfile(root / s, snapdir / Path(s).name)
