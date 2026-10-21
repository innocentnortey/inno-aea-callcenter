"""Shared loader for the handoff-information investigation. Read-only on the issued dataset."""
import re, csv, glob, os
ROOT = os.path.join(os.path.dirname(__file__), "..", "issued", "meridian_dataset")
def load():
    calls = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "call_transcripts", "*.txt"))):
        txt = open(p, encoding="utf-8").read()
        head, _, body = txt.partition("\n\n")
        hd = dict(l.split(": ", 1) for l in head.splitlines() if ": " in l)
        turns = []
        for l in body.splitlines():
            m = re.match(r"(Agent|Customer): (.*)", l)
            if m: turns.append((m.group(1), m.group(2)))
        cid = hd["Call ID"]
        calls[cid] = dict(id=cid, head=hd, turns=turns, text=" ".join(t for _, t in turns), path=p)
    return calls
def norm(s):
    s = s.lower()
    s = re.sub(r"mhc-\d+|inv-\d+|\$\d[\d,\.]*|\d+", "#", s)
    return re.sub(r"[^a-z# ]", "", s).strip()
