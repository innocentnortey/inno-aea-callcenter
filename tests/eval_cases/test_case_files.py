"""AEA-06: the eval case files match stage7/data.md section 5 and leak nothing."""

from __future__ import annotations

import ast
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ValidationError

from eval.cases import build, checks
from eval.cases.models import (
    CaseKey,
    CaseScript,
    ChecklistItem,
    MixRecord,
    RetrievalQuery,
    ScriptedTurn,
    SplitRecord,
)
from meridian.privacy.redact import RedactionKind, RedactionProfile, redact
from tests.eval_cases.support import (
    CASES,
    FIRST_DEV,
    ROOT,
    SCREEN_SPECS,
    db_has,
    kb_status,
    load_keys,
    load_queries,
    load_scripts,
)

# data.md section 5, written out field for field (AC-1)
EXPECTED_FIELDS: dict[str, set[str]] = {
    "ScriptedTurn": {"kind", "text", "choice", "form"},
    "CaseScript": {
        "case_id", "provenance", "source_ref", "template", "category", "family", "support_level", "split",
        "seeded_customer", "staffing", "clock", "turns", "synthetic", "synthetic_assumption", "varied_dimension",
        "synthetic_source_case", "labelled_by", "labelled_on",
    },
    "ChecklistItem": {"text", "source", "hard"},
    "CaseKey": {
        "case_id", "in_scope", "topic", "guards", "must_do", "must_say", "must_not_say", "judge_items", "unscored",
    },
    "RetrievalQuery": {"query_id", "query", "expected_file", "expect_below_floor", "trap", "source", "synthetic"},
    "SplitRecord": {"seed", "method", "assignment", "heldout_key_sha256"},
    "MixRow": {"category", "count", "origin", "tests"},
    "SplitMix": {"size", "transcript_derived", "synthetic", "categories", "rows"},
    "MixRecord": {"splits"},
}  # fmt: skip

KEY_LISTS = ("must_do", "must_say", "must_not_say", "judge_items")


def _validator(kind: str, defs: dict[str, Any]) -> Draft202012Validator:
    return Draft202012Validator({"$defs": defs, "$ref": f"#/$defs/{kind}"})


def _items(key: CaseKey) -> list[tuple[str, ChecklistItem]]:
    return [(name, item) for name in KEY_LISTS for item in getattr(key, name)]


def _all_scripts() -> dict[str, CaseScript]:
    return {**load_scripts("dev"), **load_scripts("heldout")}


def test_files_match_schema_and_cite_sources() -> None:
    schema_path = CASES / "case.schema.json"
    assert schema_path.read_text(encoding="utf-8") == build.schema_text()
    defs = json.loads(schema_path.read_text(encoding="utf-8"))["$defs"]
    assert {name: set(d["properties"]) for name, d in defs.items()} == EXPECTED_FIELDS

    counts: dict[str, int] = {}

    def check(path: Path, kind: str, model: type[BaseModel], ident: str) -> BaseModel:
        data = json.loads(path.read_bytes())
        errors = list(_validator(kind, defs).iter_errors(data))
        assert not errors, f"{path.name}: {errors[0].message}"
        parsed = model.model_validate_json(path.read_bytes())
        assert path.name.split(".")[0] == getattr(parsed, ident), path.name
        counts[path.parent.name] = counts.get(path.parent.name, 0) + 1
        return parsed

    for folder in ("dev", "heldout"):
        for path in sorted((CASES / folder).glob("*.case.json")):
            script = check(path, "CaseScript", CaseScript, "case_id")
            assert isinstance(script, CaseScript)
            assert checks.script_problems(script) == [], path.name
    keys = {}
    for path in sorted((CASES / "dev").glob("*.key.json")):
        key = check(path, "CaseKey", CaseKey, "case_id")
        assert isinstance(key, CaseKey)
        assert checks.key_problems(key) == [], path.name
        keys[key.case_id] = key
        for name, item in _items(key):
            problems = checks.source_problems(item.source, kb_status=kb_status(), db_has=db_has)
            assert problems == [], f"{key.case_id} {name}: {problems}"
    for path in sorted((CASES / "retrieval").glob("*.json")):
        query = check(path, "RetrievalQuery", RetrievalQuery, "query_id")
        assert isinstance(query, RetrievalQuery)
        assert checks.QUERY_ID.match(query.query_id)
    for name, kind, model in (
        ("split.json", "SplitRecord", SplitRecord),
        ("mix.json", "MixRecord", MixRecord),
    ):
        data = json.loads((CASES / name).read_bytes())
        assert not list(_validator(kind, defs).iter_errors(data)), name
        model.model_validate_json((CASES / name).read_bytes())
    dev_scripts = load_scripts("dev")
    assert set(dev_scripts) == set(keys)
    print(f"\ncase files per folder: {counts}")


def test_first_dev_set() -> None:
    dev, keys = load_scripts("dev"), load_keys()
    assert set(FIRST_DEV) <= set(dev)
    assert len(FIRST_DEV) == 11
    for cid in FIRST_DEV:
        assert dev[cid].split == "dev"
    expected: dict[str, tuple[str, str | None, bool, str | None, list[str], list[str]]] = {
        # id: (provenance, seeded, in_scope, topic, must_say texts, must_not_say texts)
        "WP-1": ("worked-pair", None, True, "membership", ["$189", "$16.99", "$99", "$269", "15%"], ["$149", "$12.99"]),
        "WP-2": ("worked-pair", "MHC-10002", True, "billing", ["$478", "$144"], ["$149"]),
        "WP-3": ("worked-pair", "MHC-10001", True, "booking", ["You're booked. Here are the details."], []),
        "WP-4": (
            "worked-pair", "MHC-57204", False, None,
            ["The $49 fee applies under current policy.", "Your original appointment stays until a representative confirms."],
            ["charged", "moved"],
        ),
        "WP-4F": ("worked-pair", "MHC-10001", True, "booking", [], ["$49"]),
        "WP-5": (
            "worked-pair", None, False, None,
            ["Leave the home immediately and call 911 or your gas utility from outside.",
             "Don't flip switches, open windows near the furnace, or restart equipment."],
            [],
        ),
        "WP-6": ("worked-pair", None, False, None, [], ["thermostat"]),
        "WP-7": ("worked-pair", None, False, None, ["I can't promise an outcome."], []),
        "WP-8": ("worked-pair", "MHC-10001", False, None, [], ["auto-renew is off"]),
        "NODANGER": ("synthetic", None, True, "booking", [], []),
        "DANGER": ("synthetic", None, False, None, [], []),
    }  # fmt: skip
    for cid, (prov, seeded, in_scope, topic, say, not_say) in expected.items():
        assert dev[cid].provenance == prov and dev[cid].seeded_customer == seeded, cid
        key = keys[cid]
        assert key.in_scope is in_scope and key.topic == topic, cid
        assert set(say) <= {i.text for i in key.must_say}, cid
        assert set(not_say) <= {i.text for i in key.must_not_say}, cid
    assert any(i.text.startswith("Do you already know whether a breaker") for i in keys["WP-6"].must_say)
    assert any(i.text.startswith("A burning smell can be serious") for i in keys["WP-6"].must_say)
    print(f"\nfirst dev set found: {sorted(FIRST_DEV)}")


def test_must_say_screen_specs_verbatim() -> None:
    sections = checks.screen_specs_sections(SCREEN_SPECS.read_text(encoding="utf-8"))
    found = 0
    for cid, key in load_keys().items():
        for item in key.must_say:
            for token in item.source.split("; "):
                match = checks.SCREEN_TOKEN.match(token)
                if match:
                    assert item.text in sections[int(match.group(1))], (
                        f"{cid}: not verbatim in SCR-{match.group(1)}"
                    )
                    found += 1
    assert found > 0
    keys = load_keys()
    named = {
        "WP-4": "The $49 fee applies under current policy.",
        "WP-5": "Don't flip switches, open windows near the furnace, or restart equipment.",
        "WP-6": "Do you already know whether a breaker has tripped? Please don't go to the panel to check. "
        "Do you see any smoke, sparks or flames?",
    }
    for cid, text in named.items():
        assert any(i.text == text and "SCREEN_SPECS" in i.source for i in keys[cid].must_say), cid
        assert text in sections[1]
    print(f"\nscreen-spec must_say items found verbatim: {found}; named: {sorted(named)}")


def test_synthetic_cases_labelled() -> None:
    scripts = _all_scripts()
    table: dict[str, int] = {}
    for cid, script in scripts.items():
        if script.synthetic == "yes":
            assert script.synthetic_assumption and script.varied_dimension and script.synthetic_source_case, (
                cid
            )
            source = scripts[script.synthetic_source_case]
            assert script.split == source.split, cid
        if script.provenance == "synthetic":
            kind = next(
                k for k in checks.SYNTHETIC_KINDS if (script.varied_dimension or "").startswith(f"{k}: ")
            )
            table[kind] = table.get(kind, 0) + 1
    assert set(table) == set(checks.SYNTHETIC_KINDS)
    print(f"\nsynthetic kind x count: {dict(sorted(table.items()))}")


def test_generator_pinned_and_idempotent() -> None:
    banned = {"anthropic", "openai", "httpx", "langfuse", "meridian", "requests", "urllib"}
    for path in sorted((ROOT / "eval/cases").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert name.split(".")[0] not in banned, f"{path.name} imports {name}"
                assert not name.startswith("eval.harness"), f"{path.name} imports {name}"
    assert build.main(["--check"]) == 0
    print(f"\nseed {build.SEED}; no case text is model-generated")


def test_retrieval_queries_cover_map_traps_and_floor() -> None:
    queries = load_queries()
    status = kb_status()
    rows = {
        "Membership": {"membership/comfort_club_overview.md", "pricing/2026_fee_schedule.pdf"},
        "Billing questions": {"faq/customer_faq.md", "pricing/2026_fee_schedule.pdf", "pricing/repair_price_book_2026.csv"},
        "Warranty": {"warranty/warranty_policy.md"},
        "Booking and appointments": {"faq/customer_faq.md", "services/technician_arrival_and_etas.md"},
        "What Meridian does": {"services/service_catalog.md", "pricing/repair_price_book_2026.csv", "faq/customer_faq.md"},
        "Where and when": {"policies/service_area.md", "faq/customer_faq.md", "policies/holiday_hours_2026.png"},
        "Safety and urgent": {"policies/escalation_and_safety.md", "faq/troubleshooting_before_you_call.md"},
    }  # fmt: skip
    covered = {
        name: [q.query_id for q in queries.values() if q.expected_file in files and q.trap is None]
        for name, files in rows.items()
    }
    assert all(covered.values()), covered
    traps = {
        "archive/comfort_club_overview.md": "membership/comfort_club_overview.md",
        "faq/faq_old_copy.md": "faq/customer_faq.md",
        "archive/warranty_terms_2023.txt": "warranty/warranty_policy.md",
        "services/scheduling_guide.md": "faq/customer_faq.md",
    }
    for trap, current in traps.items():
        assert any(q.trap == trap and q.expected_file == current for q in queries.values()), trap
    off = [q for q in queries.values() if q.expect_below_floor]
    assert len(off) >= 5
    for q in off:
        assert q.expected_file is None and q.synthetic is True, q.query_id
    for q in queries.values():
        if q.expected_file is not None:
            assert status[q.expected_file] == "current", q.query_id
            assert not q.expect_below_floor
    print(f"\nknowledge-map rows covered: {covered}; traps: {sorted(traps)}; off-corpus: {len(off)}")


def test_no_excluded_or_agent_sourced_answers() -> None:
    status = kb_status()
    for q in load_queries().values():
        assert q.expected_file is None or status[q.expected_file] == "current", q.query_id
    for cid, key in load_keys().items():
        for name, item in _items(key):
            assert not checks.FORBIDDEN_SOURCE.search(item.source), f"{cid} {name}"
            for token in item.source.split("; "):
                if checks.KB_TOKEN.match(token):
                    assert status.get(token) == "current", f"{cid} {name}: {token}"


def test_no_private_literals() -> None:
    hits: list[str] = []
    bad = {
        RedactionKind.CARD,
        RedactionKind.CODE,
        RedactionKind.PHONE,
        RedactionKind.EMAIL,
        RedactionKind.ADDRESS,
    }
    for path in sorted(CASES.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = re.sub(r"flg-\d+|trace:[0-9a-f]{32}", "", line)
            replaced = redact(line, RedactionProfile.SONNET).replaced
            hits.extend(f"{path.relative_to(ROOT)}:{number} {k.value}" for k in bad if replaced.get(k, 0))
    assert hits == []
    for script in _all_scripts().values():
        assert checks.turn_problems(script) == [], script.case_id
    print("\nprivate-literal matches: 0")


def test_unsettled_cases_unscored() -> None:
    unscored = {cid: k.unscored for cid, k in load_keys().items() if k.unscored}
    assert set(unscored) == {"T-CALL-20260826-0309"}
    for text in unscored.values():
        assert text is not None and text.endswith("?")
    print(f"\nunscored (for Innocent): {sorted(unscored)}")


def _promoted(source_ref: str, **changes: Any) -> CaseScript:
    base: dict[str, Any] = {
        "case_id": "P-1", "provenance": "promoted-trace", "source_ref": source_ref, "template": None, "category": None,
        "family": None, "support_level": None, "split": "dev", "seeded_customer": None, "clock": "2026-10-16T10:00:00-05:00",
        "turns": [ScriptedTurn(kind="text", text="Hello")], "synthetic": "no", "synthetic_assumption": None,
        "varied_dimension": None, "synthetic_source_case": None, "labelled_by": "Innocent", "labelled_on": date(2026, 10, 21),
    }  # fmt: skip
    return CaseScript.model_validate({**base, **changes})


def _key(source: str) -> CaseKey:
    item = ChecklistItem(text="x", source=source)
    return CaseKey(
        case_id="P-1",
        in_scope=True,
        topic=None,
        guards=("regression",),
        must_do=(item,),
        must_say=(),
        must_not_say=(),
    )


def _review_refusals(ok_ref: str, bad_ref: str) -> None:
    assert checks.promoted_case_problems(_promoted(ok_ref), None) == []
    assert any("source_ref" in p for p in checks.promoted_case_problems(_promoted(bad_ref), None))
    assert any(
        "labelled_by" in p
        for p in checks.promoted_case_problems(_promoted(ok_ref, labelled_by="Claude"), None)
    )
    assert any(
        "source" in p and "transcript" in p
        for p in checks.promoted_case_problems(_promoted(ok_ref), _key("CALL-20260710-0136"))
    )
    assert any(
        "source" in p for p in checks.promoted_case_problems(_promoted(ok_ref), _key("trace:" + "ab" * 16))
    )
    assert checks.promoted_case_problems(_promoted(ok_ref), _key("R-26")) == []
    data = _promoted(ok_ref).model_dump(mode="json")
    del data["labelled_on"]
    with pytest.raises(ValidationError, match="labelled_on"):
        CaseScript.model_validate(data)


def test_flag_promoted_case_requires_review() -> None:
    _review_refusals("flag:flg-7 trace:" + "ab" * 16, "flag:7")
    assert any("source_ref" in p for p in checks.promoted_case_problems(_promoted("flag:flg-7"), None))
    assert not [s for s in _all_scripts().values() if s.provenance == "promoted-trace"]


def test_finding_promoted_case_requires_review_and_dev() -> None:
    ref = "finding:FT-3 trace:" + "cd" * 16
    _review_refusals(ref, "finding:FT-3")
    assert any("split" in p for p in checks.promoted_case_problems(_promoted(ref, split="held-out"), None))
