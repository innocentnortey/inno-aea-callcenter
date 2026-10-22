"""AEA-33: FastembedIndex readiness, search and info. Also holds the shared helpers the other two AEA-33 test files import."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

from meridian.adapters.retrieval_fastembed import FastembedIndex, Readiness
from meridian.domain.records import Passage
from meridian.ports.runtime import IndexInfo
from meridian.retrieval import settings
from meridian.retrieval.ingest import build_index
from meridian.retrieval.manifest import MANIFEST, FileStatus, ManifestRow

ROOT = Path(__file__).resolve().parents[3]
KB_DIR = ROOT / "docs/data/issued/meridian_dataset/knowledge_base"
TRANSCRIPTIONS_DIR = ROOT / "data/kb_transcriptions"

FIXTURE_DIM = 4
FIXTURE_SCORES = (0.9, 0.7, 0.65, 0.5, 0.2)
QUERY_VECTOR = (1.0, 0.0, 0.0, 0.0)

_FIXTURE_ROWS: tuple[tuple[str, str, str, str | None, str], ...] = (
    (
        "membership/comfort_club_overview.md#0",
        "Comfort Club Maintenance Plan > Plans",
        "Effective 2026-01-01",
        "2026-01-01",
        "FIXTURE-PASSAGE-0 Price: $189 per year per system, or $16.99 per month",
    ),
    (
        "faq/customer_faq.md#1",
        "Meridian Home Comfort — Customer FAQ > Hours & Contact",
        "Last updated 2026-03-02",
        "2026-03-02",
        "FIXTURE-PASSAGE-1 Phone lines are open on weekdays.",
    ),
    (
        "policies/escalation_and_safety.md#0",
        "Escalation and Safety",
        "Rev 2026-01",
        None,
        "FIXTURE-PASSAGE-2 Safety first.",
    ),
    (
        "faq/troubleshooting_before_you_call.md#2",
        "Before you call",
        "undated",
        None,
        "FIXTURE-PASSAGE-3 Check the thermostat.",
    ),
    (
        "pricing/repair_price_book_2026.csv#4",
        "HVAC repair > Run capacitor replacement",
        "2026",
        None,
        "FIXTURE-PASSAGE-4 sku: HV-CAP-01",
    ),
)


def fixture_passages() -> tuple[Passage, ...]:
    return tuple(
        Passage.model_validate(
            {
                "passage_id": pid,
                "file": pid.split("#")[0],
                "section": section,
                "version_label": label,
                "version_date": date,
                "text": text,
                "score": 0.0,
            }
        )
        for pid, section, label, date, text in _FIXTURE_ROWS
    )


def fixture_vectors(scores: Sequence[float] = FIXTURE_SCORES) -> npt.NDArray[np.float32]:
    return np.asarray([[s, math.sqrt(1 - s * s), 0.0, 0.0] for s in scores], dtype=np.float32)


def fixture_manifest(n: int = 17) -> list[dict[str, object]]:
    return [
        {
            "path": f"fixture/doc_{i:02d}.md",
            "status": "current",
            "version_label": "Effective 2026-01-01",
            "parse_method": "markdown",
            "reason": None,
            "source_sha256": "0" * 64,
            "chunks": 0,
        }
        for i in range(n)
    ]


def manifest_hash(rows: Sequence[dict[str, object]]) -> str:
    dumped = [
        ManifestRow.model_validate(r).model_dump(mode="json")
        for r in sorted(rows, key=lambda r: str(r["path"]))
    ]
    return hashlib.sha256(
        json.dumps(dumped, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_settings() -> dict[str, object]:
    return {name: value for name, value in vars(settings).items() if name.isupper()}


def write_index_dir(
    index_dir: Path,
    *,
    passages: Sequence[Passage] | None = None,
    vectors: npt.NDArray[np.float32] | None = None,
    manifest: list[dict[str, object]] | None = None,
    record_overrides: dict[str, object] | None = None,
) -> Path:
    passages = fixture_passages() if passages is None else passages
    vectors = fixture_vectors() if vectors is None else vectors
    manifest = fixture_manifest() if manifest is None else manifest
    index_dir.mkdir(parents=True)
    (index_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        json.dumps(
            {**p.model_dump(mode="json", exclude={"score"}), "embed_text": p.section + "\n" + p.text},
            sort_keys=True,
            ensure_ascii=False,
        )
        for p in passages
    ]
    (index_dir / "passages.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    np.save(index_dir / "vectors.npy", vectors, allow_pickle=False)
    record: dict[str, object] = {
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "dimension": int(vectors.shape[1]),
        "chunks": len(passages),
        "manifest_hash": manifest_hash(manifest),
        "files": len(manifest),
        "settings": build_settings(),
    }
    record.update(record_overrides or {})
    (index_dir / "index_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return index_dir


class StandInEmbed:
    """Stands in for bge-small (DO-3 S-5): returns a fixed vector and records the queries."""

    def __init__(self, vector: Sequence[float] = QUERY_VECTOR) -> None:
        self.vector = tuple(vector)
        self.queries: list[str] = []

    def __call__(self, query: str) -> npt.NDArray[np.float32]:
        self.queries.append(query)
        return np.asarray(self.vector, dtype=np.float32)


def hash_embed(texts: Sequence[str]) -> npt.NDArray[np.float32]:
    rows = [
        np.frombuffer(hashlib.sha256(t.encode("utf-8")).digest()[:8], dtype=np.uint8).astype(np.float32) + 1.0
        for t in texts
    ]
    return np.stack(rows).astype(np.float32)


def cached_model_dir() -> Path | None:
    candidates: list[Path] = []
    env = os.environ.get("FASTEMBED_CACHE_PATH")
    if env:
        candidates.append(Path(env))
    candidates.append(ROOT / "var/fastembed")
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        common = Path(out)
        if not common.is_absolute():
            common = ROOT / common
        candidates.append(common.resolve().parent / "var/fastembed")
    except (OSError, subprocess.CalledProcessError):
        pass
    for c in candidates:
        if any((c / "models--Qdrant--bge-small-en-v1.5-onnx-Q" / "snapshots").glob("*/model_optimized.onnx")):
            return c
    return None


requires_model = pytest.mark.skipif(
    cached_model_dir() is None,
    reason="bge-small-en-v1.5 is not cached locally; set FASTEMBED_CACHE_PATH (tests never download)",
)


def _unlink(name: str):
    def mutate(d: Path) -> None:
        (d / name).unlink()

    return mutate


def _write(name: str, content: bytes | str):
    def mutate(d: Path) -> None:
        p = d / name
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")

    return mutate


_NO_MUTATION = None
_CASES = [
    pytest.param(_NO_MUTATION, {}, None, True, (), id="good"),
    pytest.param(_NO_MUTATION, {"__skip_write": True}, None, False, ("index_missing",), id="missing_dir"),
    pytest.param(_unlink("passages.jsonl"), {}, None, False, ("index_missing",), id="missing_passages"),
    pytest.param(
        _NO_MUTATION,
        {"record_overrides": {"dimension": 384}},
        None,
        False,
        ("dimension_mismatch",),
        id="dimension",
    ),
    pytest.param(
        _write("vectors.npy", b"not a numpy file"),
        {},
        None,
        False,
        ("dimension_mismatch",),
        id="vectors_garbage",
    ),
    pytest.param(_NO_MUTATION, {"manifest": "16"}, None, False, ("manifest_not_17",), id="manifest_16"),
    pytest.param(
        _write("manifest.json", "{not json"), {}, None, False, ("manifest_not_17",), id="manifest_garbage"
    ),
    pytest.param(
        _NO_MUTATION,
        {"record_overrides": {"chunks": 6}},
        None,
        False,
        ("record_mismatch",),
        id="record_chunks",
    ),
    pytest.param(
        _NO_MUTATION,
        {"record_overrides": {"manifest_hash": "f" * 64}},
        None,
        False,
        ("record_mismatch",),
        id="record_hash",
    ),
    pytest.param(
        _NO_MUTATION,
        {"record_overrides": {"settings": {**build_settings(), "CHUNKER": "other/0"}}},
        None,
        False,
        ("record_mismatch",),
        id="record_settings",
    ),
    pytest.param(
        _write("index_record.json", "[]"), {}, None, False, ("record_mismatch",), id="record_garbage"
    ),
]


@pytest.mark.parametrize(("mutate", "kwargs", "_unused", "expected_ok", "expected"), _CASES)
def test_readiness_failures(
    tmp_path: Path,
    mutate: object,
    kwargs: dict[str, object],
    _unused: None,
    expected_ok: bool,
    expected: tuple[str, ...],
) -> None:
    index_dir = tmp_path / "index"
    kw = dict(kwargs)
    skip_write = bool(kw.pop("__skip_write", False))
    if kw.get("manifest") == "16":
        kw["manifest"] = fixture_manifest(16)
    if not skip_write:
        write_index_dir(index_dir, **kw)  # type: ignore[arg-type]
    if callable(mutate):
        mutate(index_dir)
    embed = StandInEmbed()
    got = FastembedIndex(index_dir, embed_query=embed).readiness()
    print(f"{index_dir.name}: {got.reasons}")
    assert got == Readiness(ok=expected_ok, reasons=expected)  # type: ignore[arg-type]
    assert embed.queries == []


def test_search_and_info_refuse_when_not_ready(tmp_path: Path) -> None:
    embed = StandInEmbed()
    ix = FastembedIndex(tmp_path / "nope", embed_query=embed)
    with pytest.raises(RuntimeError, match="index_missing") as search_err:
        ix.search("x", k=3, min_score=0.6)
    with pytest.raises(RuntimeError, match="index_missing") as info_err:
        ix.info()
    assert str(tmp_path) not in str(search_err.value)
    assert str(tmp_path) not in str(info_err.value)
    assert embed.queries == []


def test_info_reads_index_record(tmp_path: Path) -> None:
    ix = FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=StandInEmbed())
    assert ix.info() == IndexInfo(
        embedding_model="BAAI/bge-small-en-v1.5",
        dimension=4,
        chunks=5,
        manifest_hash=manifest_hash(fixture_manifest()),
        files=17,
    )


def test_search_normalises_query_and_keeps_row_order_on_ties(tmp_path: Path) -> None:
    ix = FastembedIndex(write_index_dir(tmp_path / "a"), embed_query=StandInEmbed((2.0, 0.0, 0.0, 0.0)))
    got = ix.search("q", k=3, min_score=float("-inf"))
    assert [p.score for p in got.passages] == pytest.approx(list(FIXTURE_SCORES[:3]), abs=1e-6)

    tied = fixture_vectors((0.9, 0.7, 0.7, 0.5, 0.2))
    ix2 = FastembedIndex(write_index_dir(tmp_path / "b", vectors=tied), embed_query=StandInEmbed())
    ids = [p.passage_id for p in ix2.search("q", k=3, min_score=float("-inf")).passages]
    assert ids == [
        "membership/comfort_club_overview.md#0",
        "faq/customer_faq.md#1",
        "policies/escalation_and_safety.md#0",
    ]


def test_query_dimension_mismatch_raises(tmp_path: Path) -> None:
    ix = FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=StandInEmbed((1.0, 0.0, 0.0)))
    with pytest.raises(ValueError):
        ix.search("q", k=3, min_score=0.6)


def test_default_embedder_loads_nothing_until_search(tmp_path: Path) -> None:
    d = write_index_dir(tmp_path / "i")
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from meridian.adapters.retrieval_fastembed import FastembedIndex\n"
        "ix = FastembedIndex(Path(sys.argv[1]))\n"
        "ok = ix.readiness().ok\n"
        "ix.info()\n"
        "print(ok, 'fastembed' in sys.modules, 'onnxruntime' in sys.modules)\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code, str(d)], cwd=ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "True False False"


def test_readiness_ok_on_ingest_output(tmp_path: Path) -> None:
    run = build_index(KB_DIR, tmp_path / "index", transcriptions_dir=TRANSCRIPTIONS_DIR, embed=hash_embed)
    ix = FastembedIndex(tmp_path / "index", embed_query=StandInEmbed((1.0,) * 8))
    assert ix.readiness() == Readiness(ok=True, reasons=())
    info = ix.info()
    assert info.files == 17
    assert info.chunks == run.chunks
    assert info.manifest_hash == run.manifest_hash
    assert info.dimension == 8
    got = ix.search("x", k=run.chunks, min_score=float("-inf"))
    assert len(got.passages) == run.chunks
    current = {m.path for m in MANIFEST if m.status == FileStatus.CURRENT}
    banned = {
        "internal/agent_discretion_notes.md",
        "services/duct_cleaning.md",
        "faq/faq_old_copy.md",
        "services/scheduling_guide.md",
    }
    for p in got.passages:
        assert p.file in current
        assert p.file not in banned
        assert not p.file.startswith("archive/")


def test_warm_loads_index_and_embeds_once(tmp_path: Path) -> None:
    embed = StandInEmbed()
    ix = FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=embed)
    assert ix.warm() is True
    assert len(embed.queries) == 1


def test_warm_returns_false_for_missing_index(tmp_path: Path) -> None:
    embed = StandInEmbed()
    assert FastembedIndex(tmp_path / "absent", embed_query=embed).warm() is False
    assert embed.queries == []


def test_warm_returns_false_when_embedder_raises(tmp_path: Path) -> None:
    def boom(_query: str) -> npt.NDArray[np.float32]:
        raise RuntimeError("no model")

    assert FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=boom).warm() is False
