"""Image checks (AEA-50, WF-13 readiness): index readiness and one optional search, with no network.

Prints statuses, counts and document ids only; never the query or passage text.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.image_check")
    parser.add_argument("--index-dir", default=os.environ.get("MERIDIAN_INDEX_DIR", "/app/index"))
    parser.add_argument("--search", default=None, metavar="QUERY")
    args = parser.parse_args(argv)

    index = FastembedIndex(Path(args.index_dir))
    readiness = index.readiness()
    reasons = ",".join(readiness.reasons) or "-"
    sys.stdout.write(f"readiness ok={str(readiness.ok).lower()} reasons={reasons}\n")
    if not readiness.ok:
        return 1
    if args.search is not None:
        try:
            result = index.search(args.search, k=SEARCH_K, min_score=MIN_SCORE)
        except Exception as exc:
            sys.stdout.write(f"search status=error error={type(exc).__name__}\n")
            return 1
        files = ",".join(p.file for p in result.passages) or "-"
        sys.stdout.write(
            f"search status=ok passages={len(result.passages)} "
            f"below_floor={str(result.below_floor).lower()} files={files}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
