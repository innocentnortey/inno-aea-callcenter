"""Report whether the installed latin woff2 files carry tnum (all) and cv11 (Inter). Always exits 0."""
import glob
import os
import sys

from fontTools.ttLib import TTFont

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "node_modules", "@fontsource")
want = {"instrument-sans": ["tnum"], "inter": ["tnum", "cv11"], "geist-mono": ["tnum"]}
shipped = {"instrument-sans": ["600", "700"], "inter": ["400", "500", "600"], "geist-mono": ["400", "500", "600"]}
for fam, feats in want.items():
    files = [os.path.join(root, fam, "files", f"{fam}-latin-{w}-normal.woff2") for w in shipped[fam]]
    if not files:
        print(f"MISSING files {fam}")
        continue
    for f in files:
        if not os.path.exists(f):
            print(f"MISSING file {f}")
            continue
        font = TTFont(f)
        have = set()
        if "GSUB" in font:
            have = {fr.FeatureTag for fr in font["GSUB"].table.FeatureList.FeatureRecord}
        for ft in feats:
            print(f"{'ok     ' if ft in have else 'MISSING '}{ft} {fam} {os.path.basename(f)}")
sys.exit(0)
