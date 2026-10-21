"""AEA-59 fixture checks (level `mock-tested`: no server): every mock example and a generated edge set against the OpenAPI.

Every verdict comes from AEA-23's `assert_response_matches` / `assert_sse_frames_match`. A failing *allowed* variant is a
contract finding: stop and report it, never exclude it. Reads the OpenAPI and `apps/web`'s contract index; writes nothing.
"""

from __future__ import annotations

import builtins
import io
import json
import os
import re
import secrets
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from tests.api.openapi_check import (
    SseFrame,
    assert_response_matches,
    assert_sse_frames_match,
    load_contract,
    load_document,
)
from tests.api.web_shell_support import rand_word
from tests.contract.openapi_variants import (
    COUNTER_KINDS,
    REPO_ROOT,
    NamedExample,
    body_variants,
    contract_strict,
    deref,
    fake_response,
    index_mismatches,
    iter_response_examples,
    optional_response_properties,
    pointer_of,
    sse_frames,
    statuses_without_examples,
)

EXAMPLES = iter_response_examples()
JSON_EXAMPLES = [e for e in EXAMPLES if e.content_type == "application/json"]
UNKNOWN_CODE = "AEA59_NOT_A_CODE"


def _error_body(code: str) -> dict[str, Any]:
    return {
        "error": {"code": code, "field": None, "constraint": None, "details": None},
        "request_id": "req-" + uuid.uuid4().hex,
    }


def _error_statuses() -> list[tuple[str, str]]:
    """(operationId, status) for every documented JSON error status; each must use the ApiError schema."""
    found: list[tuple[str, str]] = []
    for op_id, spec in load_contract().operations.items():
        for status, schemas in spec.responses.items():
            if int(status) >= 400 and "application/json" in schemas:
                pointer = pointer_of(schemas["application/json"]["$ref"])
                if deref(pointer)[0] != "/components/schemas/ApiError":
                    pytest.fail("status schema is not ApiError; extend the error-body generator")
                found.append((op_id, status))
    return found


def check_api_fixtures(folder: Path) -> int:
    """Validate every `<operationId>.<status>.<name>.json` in `folder`; return how many were checked."""
    contract = load_contract()
    count = 0
    for path in sorted(folder.glob("*.json")):
        match = re.fullmatch(
            r"(?P<op>[A-Za-z][A-Za-z0-9]*)\.(?P<status>\d{3})\.(?P<name>[A-Za-z0-9_-]+)\.json", path.name
        )
        if match is None:
            raise AssertionError(f"{path.name}: name must be <operationId>.<status>.<name>.json")
        op, status = match["op"], match["status"]
        if op not in contract.operations:
            raise AssertionError(f"{path.name}: unknown operationId {op}")
        schemas = contract.operations[op].responses.get(status)
        if schemas is None:
            raise AssertionError(f"{path.name}: {op}: status {status} is not documented")
        content_type = next(iter(schemas)) if schemas else None
        body = json.loads(path.read_text("utf-8"))
        assert_response_matches(fake_response(status, content_type, body), op)
        count += 1
    return count


def ux_dump_path() -> tuple[Path | None, str]:
    selectors = REPO_ROOT / "docs/plans/ux-join/selectors.md"
    if not selectors.exists():
        return None, "docs/plans/ux-join/selectors.md"
    found = re.search(r"`([^`]*fixtures[^`]*\.json)`", selectors.read_text("utf-8"))
    if found is None:
        return None, "a fixtures .json path in docs/plans/ux-join/selectors.md"
    raw = found.group(1)
    path = REPO_ROOT / raw if raw.startswith("apps/") else REPO_ROOT / "apps/web" / raw
    return path, str(path.relative_to(REPO_ROOT))


def test_examples_read_as_yaml_1_2() -> None:
    doc = load_document()
    started = doc["paths"]["/api/chat/sessions"]["post"]["responses"]["201"]["content"]["application/json"][
        "examples"
    ]["STARTED"]["value"]
    assert type(started["greeting"]["at"]) is str
    assert started["greeting"]["at"] == "2026-10-16T14:20:00-05:00"
    turn = doc["paths"]["/api/chat/sessions/{thread_id}/turns"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]["BURNING_CHECK"]["value"]["blocks"][0]["options"][0]
    assert turn["option"] == "yes" and turn["label"] == "Yes"
    staffing = doc["paths"]["/api/demo/staffing"]["get"]["responses"]["200"]["content"]["application/json"]
    assert sorted(staffing["examples"]) == ["OFF", "ON"]


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda e: e.id)
def test_named_examples_match(example: NamedExample) -> None:
    if example.content_type == "application/json":
        assert_response_matches(
            fake_response(example.status, example.content_type, example.value), example.operation_id
        )
        return
    assert isinstance(example.value, str)
    frames = sse_frames(example.value)
    assert frames
    assert_sse_frames_match(frames, example.operation_id)


def test_statuses_without_examples_have_no_body() -> None:
    rows = statuses_without_examples()
    for op, status, _ in rows:
        print(f"{op} {status}")
    assert all(documents_body is False for _, _, documents_body in rows)
    assert [(op, status) for op, status, _ in rows] == [("logout", "204")]


def test_edge_variants_accepted() -> None:
    counts: Counter[str] = Counter()
    failures: list[str] = []
    for e in JSON_EXAMPLES:
        for v in body_variants(e):
            if not v.allowed:
                continue
            counts[v.kind] += 1
            try:
                assert_response_matches(fake_response(e.status, e.content_type, v.body), e.operation_id)
            except AssertionError:
                failures.append(f"{e.id} {v.kind} at {'/'.join(map(str, v.path))}")
    contract = load_contract()
    for op_id, status in _error_statuses():
        for code in sorted(contract.error_codes):
            counts["error"] += 1
            try:
                assert_response_matches(fake_response(status, "application/json", _error_body(code)), op_id)
            except AssertionError:
                failures.append(f"{op_id}/{status} error body for code {code}")
    optional = optional_response_properties()
    print(
        f"omitted={counts['omitted']} null={counts['null']} empty={counts['empty']} error={counts['error']}"
    )
    print(f"optional response properties (scan): {optional or 'none'}")
    assert failures == [], "allowed variants rejected (contract finding): " + "; ".join(failures[:20])
    assert counts["null"] > 0 and counts["empty"] > 0 and counts["error"] > 0
    assert counts["omitted"] > 0 or optional == []


def test_counter_variants_rejected() -> None:
    counts: Counter[str] = Counter()
    accepted: list[str] = []

    def must_fail(status: str, content_type: str, body: Any, op: str, label: str, kind: str) -> None:
        counts[kind] += 1
        try:
            assert_response_matches(fake_response(status, content_type, body), op)
        except AssertionError:
            return
        accepted.append(f"{label} ({kind})")

    for e in JSON_EXAMPLES:
        for v in body_variants(e):
            if not v.allowed:
                must_fail(e.status, e.content_type, v.body, e.operation_id, f"{e.id} at {v.path}", v.kind)
    for op_id, status in _error_statuses():
        must_fail(
            status, "application/json", _error_body(UNKNOWN_CODE), op_id, f"{op_id}/{status}", "unknown_code"
        )
    first_by_op: dict[str, NamedExample] = {}
    for e in JSON_EXAMPLES:
        first_by_op.setdefault(e.operation_id, e)
    for op_id, e in first_by_op.items():
        must_fail("418", e.content_type, e.value, op_id, op_id, "undocumented_status")
    print(dict(counts))
    assert accepted == [], "counter-variants accepted: " + "; ".join(accepted[:20])
    for kind in (*COUNTER_KINDS, "unknown_code", "undocumented_status"):
        assert counts[kind] > 0, kind


def test_contract_index_matches_openapi() -> None:
    problems = index_mismatches()
    assert problems == [], (
        f"apps/web/src/api/contract.gen.json is stale (OpenAPI {load_contract().version}): "
        + "; ".join(problems)
        + "; regenerate in the UX session with `npm run examples` in apps/web"
    )


def test_api_fixtures_match() -> None:
    n = check_api_fixtures(REPO_ROOT / "tests/fixtures/api")
    print(f"tests/fixtures/api: {n} files")


def test_api_fixture_names_refused(tmp_path: Path) -> None:
    cases = {
        "getQueue.418.x.json": "getQueue: status 418 is not documented",
        "noSuchOp.200.x.json": "unknown operationId noSuchOp",
        "badname.json": "name must be <operationId>.<status>.<name>.json",
    }
    for name, message in cases.items():
        folder = tmp_path / name
        folder.mkdir()
        (folder / name).write_text("{}", "utf-8")
        with pytest.raises(AssertionError, match=re.escape(message)):
            check_api_fixtures(folder)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "blocked-on AEA-23 follow-up: openapi_check failure messages embed the instance value "
        "(jsonschema error.message); AEA-59 AC-14"
    ),
)
def test_failure_messages_carry_no_values(capsys: pytest.CaptureFixture[str]) -> None:
    password = rand_word(14, "pw")
    cookie = secrets.token_urlsafe(32)
    code = f"{secrets.randbelow(10**6):06d}"
    by_id = {e.id: e for e in EXAMPLES}
    login = by_id["login/200/LOGGED_IN"].value
    inbox = by_id["listDemoInbox/200/ONE_ACTIVE"].value
    broken: list[tuple[str, Any, str, str, str]] = []
    a = json.loads(json.dumps(login))
    a["session"]["role"] = password
    broken.append(("login", a, "session/role", password, "a"))
    b = json.loads(json.dumps(login))
    b["session"]["signed_in_at"] = cookie
    broken.append(("login", b, "session/signed_in_at", cookie, "b"))
    c = json.loads(json.dumps(inbox))
    c["messages"][0]["status"] = code
    broken.append(("listDemoInbox", c, "messages/0/status", code, "c"))
    texts: list[tuple[str, str]] = []
    for op, body, pointer, secret, _ in broken:
        with pytest.raises(AssertionError) as raised:
            assert_response_matches(fake_response("200", "application/json", body), op)
        text = str(raised.value)
        texts.append((secret, text))
        assert op in text and "200" in text and pointer in text
    for secret, text in texts:
        assert secret not in text
    out = capsys.readouterr()
    for secret in (password, cookie, code):
        assert secret not in out.out + out.err
        for record in (REPO_ROOT / "docs/testing/journeys").glob("*-AEA-59.md"):
            assert secret not in record.read_text("utf-8")


def test_never_reads_eval(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[str] = []
    real_open = io.open

    def spy(file: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(file, (str, os.PathLike)):
            opened.append(os.fspath(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    monkeypatch.setattr(io, "open", spy)
    load_document.__wrapped__()
    for example in JSON_EXAMPLES[:5]:
        body_variants(example)
    check_api_fixtures(REPO_ROOT / "tests/fixtures/api")
    json.loads((REPO_ROOT / "apps/web/src/api/contract.gen.json").read_text("utf-8"))
    ux_dump_path()
    assert opened, "the spy did not see the OpenAPI being read"
    eval_root = (REPO_ROOT / "eval").resolve()
    for p in opened:
        resolved = Path(p).resolve()
        assert resolved != eval_root and eval_root not in resolved.parents, "AEA-59 must never open eval/"
    print("eval/ paths opened: 0")


def test_ux_dump_fixtures_match() -> None:
    path, label = ux_dump_path()
    if path is None or not path.exists():
        reason = f"ux fixture dump missing: {label}"
        if contract_strict():
            pytest.fail(reason)
        pytest.skip(reason)
    records = json.loads(path.read_text("utf-8"))
    assert isinstance(records, list) and all(
        isinstance(r, dict) and {"operationId", "status", "name", "body"} <= set(r) for r in records
    )
    contract = load_contract()
    failures: list[str] = []
    for r in records:
        op, status, body = r["operationId"], str(r["status"]), r["body"]
        spec = contract.operations.get(op)
        try:
            if spec is None:
                raise AssertionError(f"unknown operationId {op}")
            if spec.event_schema and status == "200":
                if isinstance(body, str):
                    frames = sse_frames(body)
                else:
                    items = body if isinstance(body, list) else [body]
                    frames = [
                        SseFrame(
                            event=str(i.get("type")),
                            id=str(i["event_id"]) if "event_id" in i else None,
                            data=json.dumps(i),
                        )
                        for i in items
                    ]
                assert_sse_frames_match(frames, op)
            else:
                schemas = spec.responses.get(status, {})
                content_type = next(iter(schemas), None)
                assert_response_matches(fake_response(status, content_type, body), op)
        except AssertionError:
            failures.append(f"{op} {status} {r['name']}")
    print(f"ux fixture dump: {len(records)} records checked")
    assert failures == [], "dev fixtures disagree with the contract: " + "; ".join(failures)
