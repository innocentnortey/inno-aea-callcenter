"""AEA-06: split, mix, held-out custody and tracking of the eval case files."""

from __future__ import annotations

import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

from eval.cases import build, seal
from eval.cases.models import CaseKey, CaseScript, MixRecord, SplitRecord, dump_canonical
from tests.eval_cases.support import CASES, ROOT, load_scripts


def _split() -> SplitRecord:
    return SplitRecord.model_validate_json((CASES / "split.json").read_bytes())


def _all() -> dict[str, CaseScript]:
    return {**load_scripts("dev"), **load_scripts("heldout")}


def test_no_template_in_both_splits() -> None:
    seen: dict[str, str] = {}
    for script in _all().values():
        if script.template is None:
            continue
        assert seen.setdefault(script.template, script.split) == script.split, script.template
    rows = build.read_call_map(ROOT)
    split = _split()
    assert set(split.assignment) == {r.template for r in rows} and len(split.assignment) == 46
    for script in _all().values():
        if script.provenance == "issued-transcript":
            assert script.template is not None and split.assignment[script.template] == script.split
    for call in build.WORKED_PAIR_CALLS.values():
        template = next(r.template for r in rows if r.call_id == call)
        assert split.assignment[template] == "dev"
    units: dict[str, set[str]] = {}
    for template, name in split.assignment.items():
        units.setdefault(build.draw_unit(template), set()).add(name)
    assert all(len(v) == 1 for v in units.values())
    dev_units = sum(1 for v in units.values() if v == {"dev"})
    print(f"\nunits {len(units)}: dev {dev_units}, held-out {len(units) - dev_units}")


def test_split_reproducible_from_seed() -> None:
    rows = build.read_call_map(ROOT)
    split = _split()
    assignment, _ = build.draw(rows, seed=split.seed)
    record = SplitRecord.model_validate(
        {
            "seed": split.seed,
            "method": build.METHOD,
            "assignment": assignment,
            "heldout_key_sha256": split.heldout_key_sha256,
        }
    )
    assert dump_canonical(record) == (CASES / "split.json").read_bytes()
    for name, folder in (("dev", "dev"), ("held-out", "heldout")):
        on_disk = {p.name.removesuffix(".case.json") for p in (CASES / folder).glob("T-*.case.json")}
        drawn = {
            f"T-{r.call_id}"
            for r in build.sample_calls(rows, build.draw(rows, split.seed)[1])
            if assignment[r.template] == name
        }
        assert on_disk == drawn
    print(f"\nseed {split.seed}; templates {len(assignment)}; dev {list(assignment.values()).count('dev')}")


def test_mix_proportional_and_published() -> None:
    rows = build.read_call_map(ROOT)
    strata: dict[tuple[str, str], int] = {}
    for r in rows:
        strata[(r.family, r.support_level)] = strata.get((r.family, r.support_level), 0) + 1
    exact = {k: Fraction(60 * n, 420) for k, n in strata.items()}
    quotas = {k: int(q) for k, q in exact.items()}
    for k in sorted(exact, key=lambda k: (-(exact[k] - quotas[k]), k))[: 60 - sum(quotas.values())]:
        quotas[k] += 1
    assert dict(sorted(quotas.items())) == build.stratum_quotas(rows)
    assert sum(quotas.values()) == 60
    taken: dict[tuple[str, str], int] = {}
    for script in _all().values():
        if script.provenance == "issued-transcript":
            assert script.family is not None and script.support_level is not None
            key = (script.family, script.support_level)
            taken[key] = taken.get(key, 0) + 1
    assert taken == quotas
    mix = MixRecord.model_validate_json((CASES / "mix.json").read_bytes())
    assert dump_canonical(build.compute_mix(list(_all().values()))) == (CASES / "mix.json").read_bytes()
    assert set(mix.splits) == {"dev", "held-out"}
    for split in mix.splits.values():
        assert split.size == split.transcript_derived + split.synthetic and split.categories
    print("\nstratum: quota vs corpus share")
    for k, q in quotas.items():
        print(f"  {k}: {q} vs {float(exact[k]):.2f}")
    print(f"mix: { {n: (s.size, s.transcript_derived, s.synthetic) for n, s in mix.splits.items()} }")


def test_no_heldout_key_in_repo() -> None:
    assert not list((CASES / "heldout").glob("*.key.json"))
    scripts = load_scripts("heldout")
    for cid in scripts:
        assert not list((ROOT / "eval").rglob(f"{cid}.key.json")), cid
    assert all(s.split == "held-out" for s in scripts.values())
    print(f"\nheld-out scripts: {len(scripts)}; held-out key files: 0")


def _fixture_keys(directory: Path, ids: tuple[str, ...] = ("FX-1", "FX-2", "FX-3")) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        key = CaseKey(
            case_id=cid,
            in_scope=True,
            topic=None,
            guards=("regression",),
            must_do=(),
            must_say=(),
            must_not_say=(),
        )
        (directory / f"{cid}.key.json").write_bytes(dump_canonical(key))


def test_heldout_hash_check(tmp_path: Path) -> None:
    import hashlib

    _fixture_keys(tmp_path)
    digest = hashlib.sha256()
    for path in sorted(tmp_path.glob("*.key.json"), key=lambda p: p.name):
        digest.update(path.read_bytes())
    computed = seal.heldout_key_sha256(tmp_path)
    assert computed == digest.hexdigest()
    assert seal.check_seal(tmp_path, computed) == computed
    target = tmp_path / "FX-2.key.json"
    original = target.read_bytes()
    target.write_bytes(original.replace(b"true", b"fals", 1))
    with pytest.raises(seal.SealMismatch):
        seal.check_seal(tmp_path, computed)
    target.write_bytes(original)
    (tmp_path / "FX-3.key.json").unlink()
    assert seal.heldout_key_sha256(tmp_path) != computed
    recorded = _split().heldout_key_sha256
    assert recorded is None or len(recorded) == 64
    print(f"\nfixture hash {computed}; edited copy refused; recorded in split.json: {recorded}")


def test_seal_record_requires_complete_key_dir(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "eval/cases/heldout").mkdir(parents=True)
    shutil.copy(CASES / "split.json", root / "eval/cases/split.json")
    for cid in ("T-CALL-20260101-0001", "T-CALL-20260101-0002"):
        (root / f"eval/cases/heldout/{cid}.case.json").write_text("{}", encoding="utf-8")
    keys = tmp_path / "keys"
    _fixture_keys(keys, ("T-CALL-20260101-0001",))
    before = (root / "eval/cases/split.json").read_bytes()
    assert seal.main(["--heldout-key-dir", str(keys), "--root", str(root), "--record"]) == 1
    assert (root / "eval/cases/split.json").read_bytes() == before
    _fixture_keys(keys, ("T-CALL-20260101-0001", "T-CALL-20260101-0002"))
    assert seal.main(["--heldout-key-dir", str(keys), "--root", str(root), "--record"]) == 0
    recorded = json.loads((root / "eval/cases/split.json").read_text(encoding="utf-8"))["heldout_key_sha256"]
    assert recorded == seal.heldout_key_sha256(keys)
    assert seal.main(["--heldout-key-dir", str(keys), "--root", str(root)]) == 0


def _git(*args: str) -> list[str]:
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        pytest.skip("not a git checkout")
    return done.stdout.splitlines()


def test_eval_set_tracked_in_repo() -> None:
    untracked = _git(
        "ls-files", "--others", "--exclude-standard", "--", "eval/cases", "docs/data/issued/meridian_dataset"
    )
    assert untracked == []
    cases = _git("ls-files", "--", "eval/cases")
    assert not [p for p in cases if p.startswith("eval/cases/heldout/") and p.endswith(".key.json")]
    dataset = _git("ls-files", "--", "docs/data/issued/meridian_dataset")
    on_disk = {
        str(p.relative_to(ROOT))
        for p in (ROOT / "eval/cases").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert on_disk == set(cases)
    print(f"\ntracked case files {len(cases)}; dataset files {len(dataset)}; untracked 0")
