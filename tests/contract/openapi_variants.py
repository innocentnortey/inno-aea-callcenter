"""OpenAPI document pointers, named examples and the generated edge-variant set (AEA-59).

Every verdict comes from AEA-23's `assert_response_matches` / `assert_sse_frames_match`; this module builds the
inputs. `jsonschema` is used here only to choose which `oneOf`/`anyOf` member an example instance matches, so a
variant is judged against the branch the UI would render. Reads the OpenAPI and `apps/web/src/api/contract.gen.json`;
writes nothing.
"""

from __future__ import annotations

import copy
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final
from urllib.parse import quote, unquote

import httpx
from jsonschema import Draft202012Validator

from tests.api.events_support import parse_sse_text
from tests.api.openapi_check import (
    CONTRACT_URI,
    JsonValue,
    SseFrame,
    load_contract,
    load_document,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
STRICT_ENV: Final = "CONTRACT_STRICT"
_METHODS: Final = ("get", "post", "put", "patch", "delete")
ALLOWED_KINDS: Final = ("omitted", "null", "empty")
COUNTER_KINDS: Final = ("required_omitted", "null_not_allowed", "empty_below_min_items")


def contract_strict() -> bool:
    """Test-only switch, read only by tests/contract/*; never by src/."""
    return os.environ.get(STRICT_ENV) == "1"


# -- document pointers ----------------------------------------------------------------------------------------
def _escape(part: str) -> str:
    return part.replace("~", "~0").replace("/", "~1")


def pointer_of(ref: str) -> str:
    """'urn:meridian:ui-contracts#/a/b%7Bx%7D' or '#/a/b' -> '/a/b{x}' (unquoted JSON pointer)."""
    return unquote(ref.split("#", 1)[1]) if "#" in ref else unquote(ref)


def node_at(pointer: str) -> Any:
    """Walk load_document() by a JSON pointer ('' is the root)."""
    node: Any = load_document()
    if pointer == "":
        return node
    for part in pointer.lstrip("/").split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node


def deref(pointer: str) -> tuple[str, Any]:
    """Follow $ref chains from the node at `pointer` (both ref forms); return (final pointer, node)."""
    node = node_at(pointer)
    for _ in range(30):
        ref = node.get("$ref") if isinstance(node, dict) else None
        if not isinstance(ref, str):
            return pointer, node
        pointer = pointer_of(ref)
        node = node_at(pointer)
    raise AssertionError(f"$ref chain too long at {pointer}")


def ref_schema(pointer: str) -> dict[str, str]:
    return {"$ref": CONTRACT_URI + "#" + quote(pointer, safe="/~")}


def resolve(node: Any) -> Any:
    """Follow '#/...' $ref chains on a document node (responses, requestBodies, examples)."""
    for _ in range(30):
        ref = node.get("$ref") if isinstance(node, dict) else None
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return node
        node = node_at(ref[1:])
    raise AssertionError("$ref chain too long")


# -- named examples -------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class NamedExample:
    operation_id: str
    status: str
    content_type: str
    name: str
    value: JsonValue
    schema_pointer: str

    @property
    def id(self) -> str:
        return f"{self.operation_id}/{self.status}/{self.name}"


def _operations_in_order() -> list[tuple[str, str, str, Any]]:
    """(path, method, operationId, operation node) in document order."""
    found: list[tuple[str, str, str, Any]] = []
    for path, item in load_document()["paths"].items():
        for method in _METHODS:
            operation = item.get(method)
            if isinstance(operation, dict) and "operationId" in operation:
                found.append((path, method, operation["operationId"], operation))
    return found


def iter_response_examples() -> list[NamedExample]:
    """Every named response example of every operation and status, in document order."""
    contract = load_contract()
    found: list[NamedExample] = []
    for _path, _method, op_id, operation in _operations_in_order():
        spec = contract.operations[op_id]
        for status, raw in operation["responses"].items():
            response = resolve(raw)
            for content_type, media in (response.get("content") or {}).items():
                for name, example in (media.get("examples") or {}).items():
                    schemas = spec.responses[str(status)]
                    found.append(
                        NamedExample(
                            operation_id=op_id,
                            status=str(status),
                            content_type=content_type,
                            name=str(name),
                            value=resolve(example)["value"],
                            schema_pointer=pointer_of(schemas[content_type]["$ref"]),
                        )
                    )
    return found


def statuses_without_examples() -> list[tuple[str, str, bool]]:
    """(operationId, status, documents_a_body) for each documented status none of whose content types has an example."""
    rows: list[tuple[str, str, bool]] = []
    for _path, _method, op_id, operation in _operations_in_order():
        for status, raw in operation["responses"].items():
            content = resolve(raw).get("content") or {}
            if not any(media.get("examples") for media in content.values()):
                rows.append((op_id, str(status), bool(content)))
    return rows


def operation_node(operation_id: str) -> Any:
    spec = load_contract().operations[operation_id]
    return load_document()["paths"][spec.path_template][spec.method]


def request_examples(operation_id: str) -> dict[str, JsonValue]:
    """{name: deep copy of the example value} for the op's application/json requestBody examples; {} when none."""
    body = operation_node(operation_id).get("requestBody")
    if body is None:
        return {}
    media = (resolve(body).get("content") or {}).get("application/json") or {}
    return {
        str(name): copy.deepcopy(resolve(example)["value"])
        for name, example in (media.get("examples") or {}).items()
    }


def fake_response(status: str | int, content_type: str | None, body: JsonValue | None) -> httpx.Response:
    """An httpx.Response carrying the status, content type and an X-Request-ID (the body's own when it has one)."""
    request_id = body.get("request_id") if isinstance(body, dict) else None
    headers = {"X-Request-ID": request_id if isinstance(request_id, str) else "req-" + uuid.uuid4().hex}
    if content_type is not None:
        headers["content-type"] = content_type
    content = b"" if body is None else json.dumps(body).encode()
    return httpx.Response(int(status), headers=headers, content=content)


def sse_frames(text: str) -> list[SseFrame]:
    return [item for item in parse_sse_text(text) if isinstance(item, SseFrame)]


# -- the contract index apps/web builds -----------------------------------------------------------------------
def index_mismatches() -> list[str]:
    """Differences between apps/web/src/api/contract.gen.json and the OpenAPI, as 'op: field differs' lines."""
    contract = load_contract()
    index = json.loads((REPO_ROOT / "apps/web/src/api/contract.gen.json").read_text("utf-8"))
    problems: list[str] = []
    if index.get("specVersion") != contract.version:
        problems.append(f"specVersion {index.get('specVersion')!r} != {contract.version!r}")
    indexed = index.get("operations") or {}
    if sorted(indexed) != sorted(contract.operations):
        problems.append(
            "operation set differs: " + ", ".join(sorted(set(indexed) ^ set(contract.operations)))
        )
    for op_id, spec in contract.operations.items():
        entry = indexed.get(op_id)
        if entry is None:
            continue
        success = sorted(int(s) for s in spec.responses if 200 <= int(s) < 300)
        if str(entry.get("method", "")).lower() != spec.method:
            problems.append(f"{op_id}: method differs")
        if entry.get("path") != spec.path_template:
            problems.append(f"{op_id}: path differs")
        if sorted(int(s) for s in entry.get("success", [])) != success:
            problems.append(f"{op_id}: success statuses differ")
        if entry.get("requestExamples", {}) != request_examples(op_id):
            problems.append(f"{op_id}: requestExamples differ")
    return problems


# -- the edge-variant generator -------------------------------------------------------------------------------
@dataclass(frozen=True)
class Variant:
    kind: str
    path: tuple[str | int, ...]
    body: JsonValue

    @property
    def allowed(self) -> bool:
        return self.kind in ALLOWED_KINDS


def _views(ptr: str, inst: Any) -> list[str]:
    ptr, node = deref(ptr)
    out = [ptr]
    if not isinstance(node, dict):
        return out
    for i in range(len(node.get("allOf") or [])):
        out.extend(_views(f"{ptr}/allOf/{i}", inst))
    for key in ("oneOf", "anyOf"):
        for i in range(len(node.get(key) or [])):
            member = f"{ptr}/{key}/{i}"
            if Draft202012Validator(ref_schema(member), registry=load_contract().registry).is_valid(inst):
                out.extend(_views(member, inst))
    return out


def _admits_null(ptr: str) -> bool:
    ptr, node = deref(ptr)
    if not isinstance(node, dict):
        return True
    declared = node.get("type")
    if declared == "null" or (isinstance(declared, list) and "null" in declared):
        return True
    if "const" in node and node["const"] is None:
        return True
    if None in (node.get("enum") or []):
        return True
    for key in ("oneOf", "anyOf"):
        if any(_admits_null(f"{ptr}/{key}/{i}") for i in range(len(node.get(key) or []))):
            return True
    all_of = node.get("allOf") or []
    if all_of and all(_admits_null(f"{ptr}/allOf/{i}") for i in range(len(all_of))):
        return True
    constraining = ("type", "properties", "items", "enum", "const", "oneOf", "anyOf", "allOf", "$ref")
    return not any(k in node for k in constraining)


def _walk(
    ptr: str, inst: Any, path: tuple[str | int, ...], out: list[tuple[str, tuple[str | int, ...]]]
) -> None:
    views = _views(ptr, inst)
    if isinstance(inst, dict):
        props: dict[str, str] = {}
        required: set[str] = set()
        for view in views:
            node = deref(view)[1]
            if not isinstance(node, dict):
                continue
            for name in node.get("properties") or {}:
                props.setdefault(name, f"{view}/properties/{_escape(name)}")
            required.update(node.get("required") or [])
        first_required = next((k for k in inst if k in required), None)
        if first_required is not None:
            out.append(("required_omitted", (*path, first_required)))
        null_counter_done = False
        for key, value in inst.items():
            prop = props.get(key)
            if prop is None:
                continue
            if key not in required:
                out.append(("omitted", (*path, key)))
            if value is not None:
                if _admits_null(prop):
                    out.append(("null", (*path, key)))
                elif not null_counter_done:
                    out.append(("null_not_allowed", (*path, key)))
                    null_counter_done = True
            _walk(prop, value, (*path, key), out)
    elif isinstance(inst, list):
        found = next((v for v in views if isinstance(deref(v)[1], dict) and "items" in deref(v)[1]), None)
        if found is None:
            return
        view = found
        node = deref(view)[1]
        if inst:
            out.append(("empty" if not node.get("minItems") else "empty_below_min_items", path))
            for i, item in enumerate(inst):
                _walk(f"{view}/items", item, (*path, i), out)


def _apply(body: Any, kind: str, path: tuple[str | int, ...]) -> Any:
    if not path:
        return []
    root = copy.deepcopy(body)
    parent = root
    for part in path[:-1]:
        parent = parent[part]
    last = path[-1]
    if kind in ("omitted", "required_omitted"):
        del parent[last]
    elif kind in ("null", "null_not_allowed"):
        parent[last] = None
    else:
        parent[last] = []
    return root


def body_variants(example: NamedExample) -> list[Variant]:
    """Allowed and counter variants of one JSON example. SSE examples get none (their value is frame text)."""
    if example.content_type != "application/json":
        return []
    found: list[tuple[str, tuple[str | int, ...]]] = []
    _walk(example.schema_pointer, example.value, (), found)
    return [Variant(kind, path, _apply(example.value, kind, path)) for kind, path in found]


def optional_response_properties() -> list[str]:
    """Pointers of every response-reachable property that is not `required` (expected today: none)."""
    optional: set[str] = set()
    seen: set[str] = set()

    def visit(ptr: str) -> None:
        ptr, node = deref(ptr)
        if ptr in seen or not isinstance(node, dict):
            return
        seen.add(ptr)
        required = set(node.get("required") or [])
        for name in node.get("properties") or {}:
            if name not in required:
                optional.add(f"{ptr}/{name}")
            visit(f"{ptr}/properties/{_escape(name)}")
        if "items" in node:
            visit(f"{ptr}/items")
        if "contentSchema" in node:
            visit(f"{ptr}/contentSchema")
        for key in ("allOf", "oneOf", "anyOf"):
            for i in range(len(node.get(key) or [])):
                visit(f"{ptr}/{key}/{i}")

    for spec in load_contract().operations.values():
        for schemas in spec.responses.values():
            for schema in schemas.values():
                visit(pointer_of(schema["$ref"]))
    return sorted(optional)
