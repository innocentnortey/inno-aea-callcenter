"""Parse the five UX-3 sources for gen_ux3.py, and guard against drift.

Read from the Markdown / YAML at every build (so it cannot go stale):
  IA.md            per-screen primary / secondary / on-demand rows, the rules and breakpoints tables
  SCREEN_SPECS.md  each card's purpose, stories, route, regions, eight states (and every n/a with its reason),
                   flow states, contracts; the state matrix and its count; flow-state coverage; N-1..N-27
  UI_CONTRACTS.md  the contract map, both named-error tables, each CON card's header lines, the data classes,
                   where each N landed, the DO-4 (UXR) table, the open items
  ui-contracts.openapi.yaml  every operation (operationId, method, path, x-con)
  design.md        primitives, semantic tokens (light/dark), the computed-contrast tables, the type scale and time
                   styles, the mint decision table, the house-texture check, the token tally
HAND-MAINTAINED in gen_ux3.py (and therefore snapshotted here): the story, the "why" prose, the hover notes on the
region callouts, the SVG layout (positions only; every label comes from the parse), the decision and ask cards.
snapshot_guard() keeps a copy of each source as last accepted; when one changes it prints the diff and stops.
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
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    return s.replace("`", "").replace("**", "").strip()


def split_row(ln):
    ln = ln.strip().replace("\\|", "\u0001")
    cells = [c.strip().replace("\u0001", "|") for c in ln.strip("|").split("|")]
    return cells


def table_rows(lines, header=False):
    out, hdr = [], None
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|\s*:?-", s):
            continue
        row = split_row(s)
        if hdr is None:
            hdr = row
            continue
        out.append(row)
    return (hdr, out) if header else out


def section(text, start_pat, end_pat=r"^## "):
    m = re.search(start_pat, text, re.M)
    if not m:
        raise SystemExit(f"source parse: section {start_pat!r} not found")
    rest = text[m.end():]
    e = re.search(end_pat, rest, re.M)
    return rest[: e.start()] if e else rest


def cards(text, pat):
    """Split `### ID · title` cards. Returns list of (id, title, body)."""
    ms = list(re.finditer(pat, text, re.M))
    out = []
    for i, m in enumerate(ms):
        end = len(text)
        nxt = re.search(r"^(### |## |---$)", text[m.end():], re.M)
        if nxt:
            end = m.end() + nxt.start()
        out.append((m.group(1), m.group(2).strip(), text[m.end():end]))
    return out


# ------------------------------------------------------------------ IA.md
def parse_ia(text):
    rules = table_rows(section(text, r"^## Rules that apply to every screen").splitlines())
    breaks_hdr, breaks = table_rows(section(text, r"^## Layout breakpoints").splitlines(), header=True)
    screens = {}
    for sid, title, body in cards(text, r"^### (SCR-\d+) · (.+)$"):
        lines = body.strip().splitlines()
        meta = lines[0].strip() if lines else ""
        paras = re.findall(r"^\*\*(Phone height budget[^\n]*(?:\n(?!\||\n)[^\n]*)*)", body, re.M)
        budget = norm(strip_md("**" + paras[0])) if paras else ""
        lap = re.findall(r"^\*\*(Laptop[^\n]*(?:\n(?!\||\n)[^\n]*)*)", body, re.M)
        laptop = norm(strip_md("**" + lap[0])) if lap else ""
        rows = []
        for r in table_rows(body.splitlines()):
            if len(r) == 4:
                rows.append({"level": r[0], "content": r[1], "why": r[2], "phone": r[3]})
        screens[sid] = {"title": title, "meta": strip_md(meta), "budget": budget, "laptop": laptop, "rows": rows}
    return {"rules": rules, "breaks_hdr": breaks_hdr, "breaks": breaks, "screens": screens}


# ------------------------------------------------------------------ SCREEN_SPECS.md
STATES = ["default", "empty", "loading", "partial", "error", "stale", "success", "disabled"]


def _bullet(body, label):
    m = re.search(rf"^- {label}: (.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def _table_after(body, label):
    m = re.search(rf"^- {label}[^\n]*:\s*$", body, re.M)
    if not m:
        return []
    out = []
    for ln in body[m.end():].splitlines():
        if ln.strip() == "":
            if out:
                break
            continue
        if ln.lstrip().startswith("|"):
            out.append(ln)
        elif out:
            break
        elif not ln.startswith(" "):
            break
    return table_rows(out)


def parse_specs(text):
    cds = {}
    for sid, title, body in cards(text, r"^### (SCR-\d+) · (.+)$"):
        if sid in cds:
            continue
        sm = _bullet(body, "Stories")
        stories, _, flows = sm.partition(" · Flows:")
        states = {}
        for r in _table_after(body, "States"):
            if len(r) >= 3:
                states[r[0].strip().lower()] = {"looks": r[1], "from": r[2]}
        regions = [{"id": r[0], "content": r[1], "con": r[2]} for r in _table_after(body, "Regions and content") if len(r) >= 3]
        flow_states = [r for r in _table_after(body, "Flow states") if len(r) >= 5]
        cds[sid] = {"title": title, "purpose": _bullet(body, "Purpose"), "stories": stories.replace("Stories:", "").strip(),
                    "flows": flows.strip(), "route": strip_md(_bullet(body, "Route")), "regions": regions,
                    "states": states, "flow_states": flow_states, "contracts": _bullet(body, "Contracts"),
                    "components": _bullet(body, "Components")}
    matrix_txt = section(text, r"^## State matrix")
    hdr, mrows = table_rows(matrix_txt.splitlines(), header=True)
    matrix = {}
    for r in mrows:
        m = re.match(r"(SCR-\d+) (.+)", r[0])
        matrix[m.group(1)] = {"name": m.group(2), "cells": dict(zip(STATES, r[1:9]))}
    count_line = re.search(r"\*\*Count:\*\*[^\n]+", matrix_txt).group(0)
    cov = table_rows(section(text, r"^## Flow-state coverage").splitlines())
    needs = table_rows(section(text, r"^## Contract needs raised").splitlines())
    notes = re.findall(r"^\d+\. \*\*(.+?)\*\*", section(text, r"^## Notes for the orchestrating session"), re.M)
    copy_rules = table_rows(section(text, r"^## Copy rules that apply on every screen", r"^---").splitlines())
    return {"cards": cds, "matrix": matrix, "count_line": strip_md(count_line), "coverage": cov, "needs": needs,
            "notes": notes, "copy_rules": copy_rules}


# ------------------------------------------------------------------ UI_CONTRACTS.md
def parse_contracts(text):
    cmap = []
    for r in table_rows(section(text, r"^## Contract map").splitlines()):
        prim = re.sub(r"\(.*?\)", "", r[1])
        cmap.append({"screen": r[0], "cons": re.findall(r"CON-\d+", prim), "extra": re.findall(r"CON-\d+", "".join(re.findall(r"\(.*?\)", r[1]))),
                     "ops": [o.strip() for o in r[2].split(",")]})
    ne = section(text, r"^## Named errors, and what each screen does")
    parts = re.split(r"^\*\*HTTP errors", ne, flags=re.M)
    composed = [r for r in table_rows(parts[0].splitlines()) if len(r) == 3]
    http = [r for r in table_rows(parts[1].splitlines()) if len(r) == 4]
    renamed = re.search(r"Names from the screen specs and DO-4 that were \*\*renamed[^\n]+", ne)
    con_cards = {}
    for cid, title, body in cards(text, r"^### (CON-\d+) · (.+)$"):
        def b(label):
            m = re.search(rf"^- {label}[^:\n]*: (.+)$", body, re.M)
            return m.group(1).strip() if m else ""
        con_cards[cid] = {"title": title, "screens": b("Screens"), "ops": b("Operations"), "access": b("Access"),
                          "timing": b("Timing budget"), "data": b("Data class and where it may go"),
                          "status": b("Status"), "guarantees": b("Guarantees")}
    classes = table_rows(section(text, r"^\*\*Data classes\*\*", r"^\*\*Access\.\*\*").splitlines(), header=True)
    landing = table_rows(section(text, r"^## Contract needs N-1").splitlines())
    uxr = [r for r in table_rows(section(text, r"^## DO-4 requests").splitlines()) if r and r[0].startswith("UXR")]
    settled = norm(strip_md(section(text, r"^## Settled at §6", r"^## ")))
    closed = [strip_md(norm(x)) for x in re.findall(r"^- (.+)$", section(text, r"^## Closed by R-48", r"^## "), re.M)]
    waiting = [strip_md(norm(section(text, r"^## Still open", r"^## ")))]
    notes = [strip_md(norm(x)) for x in re.findall(r"^- (.+)$", section(text, r"^## Other notes", r"^## "), re.M)]
    um = re.search(r"\*\*`unknown`:\*\*[^\n]+", text)
    unknown = strip_md(um.group(0)) if um else ""
    rejected_none = bool(re.search(r"\*\*Rejected: none", text))
    ops29 = re.search(r"OpenAPI 3\.1, (\d+) operations", text)
    return {"map": cmap, "composed": composed, "http": http, "renamed": strip_md(renamed.group(0)) if renamed else "",
            "cons": con_cards, "classes": classes, "landing": landing, "uxr": uxr, "unknown": unknown,
            "settled": settled, "waiting": waiting, "closed_r48": closed, "notes": notes, "rejected_none": rejected_none, "stated_ops": int(ops29.group(1)) if ops29 else None,
            "block_types": len(re.findall(r"^  \| `[a-z_]+` \|", section(text, r"^### CON-2 ", r"^### CON-3"), re.M)) - 1}


# ------------------------------------------------------------------ OpenAPI
def parse_openapi(text):
    ops, path, method, cur = [], None, None, None
    for ln in text.splitlines():
        m = re.match(r"^  (/api\S*):\s*$", ln)
        if m:
            path = m.group(1)
            continue
        m = re.match(r"^    (get|post|put|patch|delete):\s*$", ln)
        if m and path:
            method = m.group(1).upper()
            cur = {"method": method, "path": path}
            ops.append(cur)
            continue
        if cur is not None:
            m = re.match(r"^      operationId: (\S+)", ln)
            if m:
                cur["id"] = m.group(1)
            m = re.match(r"^      x-con: (CON-\d+)", ln)
            if m:
                cur["con"] = m.group(1)
            if re.match(r"^      x-demo-only: true", ln):
                cur["demo"] = True
        if re.match(r"^(components|security):", ln):
            cur = None
    ver = re.search(r"^openapi: (\S+)", text, re.M).group(1)
    return ops, ver


# ------------------------------------------------------------------ design.md
def parse_design(text):
    d = {}
    d["tally"] = strip_md(re.search(r"\*\*Token tally\*\*[^\n]+", text).group(0))
    d["primitives"] = table_rows(section(text, r"^### 4\.1 Primitives", r"^### ").splitlines())
    d["semantic"] = table_rows(section(text, r"^### 4\.2 Semantic colour tokens", r"^### ").splitlines())
    ct = section(text, r"^### 4\.3 Computed contrast", r"^### ")
    d["text_pairs"] = table_rows(section(ct, r"^#### Text pairs", r"^#### ").splitlines())
    d["ui_pairs"] = table_rows(section(ct, r"^#### UI parts", r"^#### ").splitlines())
    low = re.search(r"\*\*Lowest values:\*\*[^\n]+(?:\n(?!\n)[^\n]+)*", ct)
    d["lowest"] = strip_md(norm(low.group(0))) if low else ""
    d["type_scale"] = table_rows(section(text, r"^### 3\.2 Type scale", r"^### ").splitlines())
    d["time_styles"] = table_rows(section(text, r"^### 3\.3 The four time styles", r"^### ").splitlines())
    d["fonts"] = table_rows(section(text, r"^### 3\.1 Families", r"^### ").splitlines())
    mint = section(text, r"^### 4\.6 Mint has one meaning", r"^---")
    d["mint_rows"] = table_rows(mint.splitlines())
    d["mint_why"] = norm(strip_md(re.search(r"\*\*Why this answer and not the other\.\*\*(.+?)(?:\n\n|\Z)", mint, re.S).group(1)))
    d["mint_conflict"] = norm(strip_md(re.search(r"\*\*The conflict\.\*\*(.+?)(?:\n\n|\Z)", mint, re.S).group(1)))
    ht = section(text, r"^## 12\. House-texture check", r"^---")
    d["texture"] = table_rows(ht.splitlines())
    d["texture_result"] = norm(strip_md(re.search(r"\*\*Result:[^\n]+(?:\n(?!\n)[^\n]+)*", ht).group(0)))
    d["edge_note"] = norm(strip_md(re.search(r"- \*\*`border-control`\*\* is new in this file\.(.+?)(?:\n- )", ct + "\n- ", re.S).group(1)))
    d["differs"] = table_rows(section(text, r"^## 13\. What differs", r"^---").splitlines())
    d["upstream"] = re.findall(r"^\d+\. \*\*(.+?)\*\*", section(text, r"^## 14\. Upstream issues", r"^---"), re.M)
    d["status"] = strip_md(re.search(r"^> \*\*Status:\*\*([^\n]+)", text, re.M).group(1))
    return d


# ------------------------------------------------------------------ snapshot guard
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
            "The page's story, hover notes, callout positions, decision and ask cards are hand-maintained.\n"
            "Read the diff above, update gen_ux3.py where it is affected, then re-run with --accept-changes.\n"
            "Never just re-stamp the hashes.")


def accept_snapshots(root, sources, snapdir):
    snapdir.mkdir(exist_ok=True)
    for s in sources:
        shutil.copyfile(root / s, snapdir / Path(s).name)
