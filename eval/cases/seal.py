"""Held-out key hash and seal check (AEA-06; stage7/data.md §5, DAT-2 option B).

``python -m eval.cases.seal --heldout-key-dir PATH [--record]``. Never prints a key file's content.
"""

from __future__ import annotations

import argparse
import hashlib
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from eval.cases.checks import key_problems
from eval.cases.models import CaseKey, SplitRecord, dump_canonical

KEY_SUFFIX = ".key.json"
SCRIPT_SUFFIX = ".case.json"


class SealMismatch(Exception):
    """The key directory's hash differs from the recorded one."""


def _key_files(key_dir: Path) -> list[Path]:
    return sorted(
        (p for p in key_dir.iterdir() if p.is_file() and p.name.endswith(KEY_SUFFIX)), key=lambda p: p.name
    )


def heldout_key_sha256(key_dir: Path) -> str:
    """SHA-256 over the sorted key files' bytes: every regular '*.key.json' directly in key_dir, by file name."""
    if not key_dir.is_dir():
        raise FileNotFoundError(key_dir)
    files = _key_files(key_dir)
    if not files:
        raise ValueError(f"no key files in {key_dir}")
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def check_seal(key_dir: Path, recorded: str) -> str:
    """Return the computed hash; raise SealMismatch when it differs from the recorded one."""
    computed = heldout_key_sha256(key_dir)
    if computed != recorded:
        raise SealMismatch(f"held-out key hash mismatch: recorded {recorded} computed {computed}")
    return computed


def _record_problems(root: Path, key_dir: Path) -> list[str]:
    scripts = {p.name[: -len(SCRIPT_SUFFIX)] for p in (root / "eval/cases/heldout").glob(f"*{SCRIPT_SUFFIX}")}
    keys = {p.name[: -len(KEY_SUFFIX)]: p for p in _key_files(key_dir)}
    problems = [f"missing key for {cid}" for cid in sorted(scripts - keys.keys())]
    problems += [f"key without held-out script: {cid}" for cid in sorted(keys.keys() - scripts)]
    for cid, path in sorted(keys.items()):
        try:
            key = CaseKey.model_validate_json(path.read_bytes())
        except ValidationError:
            problems.append(f"invalid key: {cid}")
            continue
        if key.case_id != cid or key_problems(key):
            problems.append(f"invalid key: {cid}")
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or record the held-out key hash.")
    parser.add_argument("--heldout-key-dir", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--record", action="store_true", help="write the hash into split.json")
    args = parser.parse_args(argv)
    split_path: Path = args.root / "eval/cases/split.json"
    record = SplitRecord.model_validate_json(split_path.read_bytes())
    if args.record:
        problems = _record_problems(args.root, args.heldout_key_dir)
        if problems:
            for line in problems:
                print(line)
            return 1
        digest = heldout_key_sha256(args.heldout_key_dir)
        split_path.write_bytes(dump_canonical(record.model_copy(update={"heldout_key_sha256": digest})))
        print(digest)
        return 0
    if record.heldout_key_sha256 is None:
        print("no held-out key hash recorded")
        return 2
    try:
        print(check_seal(args.heldout_key_dir, record.heldout_key_sha256))
    except SealMismatch as exc:
        print(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
