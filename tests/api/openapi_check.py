"""The one OpenAPI response validator (web.md section 13, R-W-9, AEA-23-1). Every route ticket uses it.

Reads `docs/ux/03-structure/ui-contracts.openapi.yaml` (never writes it) with `ContractLoader`, a YAML 1.2 reader:
plain `yaml.safe_load` would turn timestamps into datetime objects, `yes`/`no`/`on`/`off`/`ON`/`OFF` into booleans and
`22:00` into the integer 1320. Failures are `AssertionError`s that start with the OpenAPI version and the operation id.
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import quote

import jsonschema
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "ux" / "03-structure" / "ui-contracts.openapi.yaml"
)
CONTRACT_URI = "urn:meridian:ui-contracts"
_METHODS = ("get", "post", "put", "patch", "delete")
_TAG = "tag:yaml.org,2002:"

JsonValue = Any


class ContractLoader(yaml.SafeLoader):
    """YAML 1.2 style resolution: no timestamps; booleans only true/false; JSON-style ints and floats."""


ContractLoader.yaml_implicit_resolvers = {
    first: [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag not in (_TAG + "timestamp", _TAG + "bool", _TAG + "int", _TAG + "float")
    ]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
ContractLoader.add_implicit_resolver(
    _TAG + "bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF")
)
ContractLoader.add_implicit_resolver(
    _TAG + "int",
    re.compile(r"^(?:[-+]?(?:0|[1-9][0-9]*)|0o[0-7]+|0x[0-9a-fA-F]+)$"),
    list("-+0123456789"),
)
ContractLoader.add_implicit_resolver(
    _TAG + "float",
    re.compile(
        r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"
    ),
    list("-+.0123456789"),
)


@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    method: Literal["get", "post", "put", "patch", "delete"]
    path_template: str
    responses: Mapping[
        str, Mapping[str, JsonValue]
    ]  # status -> {content type -> schema object}; {} when no content
    event_schema: str | None  # "ChatEvent" / "CaseEvent" for the two SSE operations


@dataclass(frozen=True)
class Contract:
    source: Path
    version: str
    operations: Mapping[str, OperationSpec]
    error_codes: frozenset[str]
    registry: Registry[Any]


@dataclass(frozen=True)
class SseFrame:
    event: str | None
    id: str | None
    data: str


class _ResponseLike(Protocol):
    @property
    def status_code(self) -> int: ...
    @property
    def headers(self) -> Any: ...
    @property
    def content(self) -> bytes: ...

    def json(self) -> Any: ...


@functools.cache
def load_document() -> Mapping[str, Any]:
    document = yaml.load(CONTRACT_PATH.read_text("utf-8"), Loader=ContractLoader)  # noqa: S506 (a SafeLoader subclass)
    assert isinstance(document, dict)
    return document


def _escape(part: str) -> str:
    return part.replace("~", "~0").replace("/", "~1")


def _pointer(base: str, content_type: str) -> str:
    return f"{base}/content/{_escape(content_type)}/schema"


def _ref_schema(pointer: str) -> dict[str, str]:
    return {"$ref": CONTRACT_URI + "#" + quote(pointer, safe="/~")}


def _resolve_response(
    document: Mapping[str, Any], response: Mapping[str, Any], base: str
) -> tuple[Mapping[str, Any], str]:
    ref = response.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        target = document
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return target, ref[1:]
    return response, base


@functools.cache
def load_contract() -> Contract:
    document = load_document()
    operations: dict[str, OperationSpec] = {}
    for path, item in document["paths"].items():
        for method in _METHODS:
            operation = item.get(method)
            if not isinstance(operation, dict) or "operationId" not in operation:
                continue
            responses: dict[str, Mapping[str, JsonValue]] = {}
            event_schema: str | None = None
            for status, raw in operation["responses"].items():
                base = f"/paths/{_escape(path)}/{method}/responses/{status}"
                response, response_base = _resolve_response(document, raw, base)
                content = response.get("content") or {}
                responses[str(status)] = {
                    content_type: _ref_schema(_pointer(response_base, content_type))
                    for content_type in content
                }
                stream = content.get("text/event-stream") if str(status) == "200" else None
                if stream is not None:
                    ref = (stream.get("schema", {}).get("contentSchema") or {}).get("$ref")
                    if isinstance(ref, str):
                        event_schema = ref.rsplit("/", 1)[1]
            operations[operation["operationId"]] = OperationSpec(
                operation_id=operation["operationId"],
                method=method,  # type: ignore[arg-type]
                path_template=path,
                responses=responses,
                event_schema=event_schema,
            )
    error_codes = frozenset(
        document["components"]["schemas"]["ApiError"]["properties"]["error"]["properties"]["code"]["enum"]
    )
    registry: Registry[Any] = Registry().with_resource(
        CONTRACT_URI, Resource.from_contents(document, default_specification=DRAFT202012)
    )
    return Contract(
        source=CONTRACT_PATH,
        version=str(document["info"]["version"]),
        operations=operations,
        error_codes=error_codes,
        registry=registry,
    )


def _build_formats() -> jsonschema.FormatChecker:
    checker = jsonschema.FormatChecker()

    @checker.checks("date-time", raises=ValueError)
    def _date_time(value: object) -> bool:
        if not isinstance(value, str):
            return True
        if "T" not in value:
            raise ValueError("date-time needs a T")
        if not (value.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", value)):
            raise ValueError("date-time needs a UTC offset or Z")
        datetime.fromisoformat(value)
        return True

    return checker


_FORMATS = _build_formats()


def _fail(contract: Contract, operation_id: str, message: str) -> AssertionError:
    return AssertionError(f"[OpenAPI {contract.version}] {operation_id}: {message}")


def assert_response_matches(response: _ResponseLike, operation_id: str) -> None:
    contract = load_contract()
    spec = contract.operations.get(operation_id)
    if spec is None:
        raise _fail(contract, operation_id, "no such operation in the OpenAPI")
    status = str(response.status_code)
    if status not in spec.responses:
        raise _fail(
            contract,
            operation_id,
            f"status {status} is not documented (documented: {sorted(spec.responses)})",
        )
    schemas = spec.responses[status]
    body: Any = None
    if not schemas:
        if response.content:
            raise _fail(contract, operation_id, f"status {status} documents no body, but one was sent")
    else:
        content_type = str(response.headers.get("content-type", "")).split(";")[0].strip()
        if content_type not in schemas:
            raise _fail(
                contract,
                operation_id,
                f"content type {content_type!r} is not documented for {status} (documented: {sorted(schemas)})",
            )
        body = response.json()
        validator = Draft202012Validator(
            schemas[content_type], registry=contract.registry, format_checker=_FORMATS
        )
        for error in validator.iter_errors(body):
            where = "/".join(str(part) for part in error.absolute_path) or "(body)"
            raise _fail(
                contract, operation_id, f"{status} body breaks the schema at {where}: {error.message[:200]}"
            )
    if "X-Request-ID" not in response.headers:
        raise _fail(contract, operation_id, "the X-Request-ID header is missing")
    if isinstance(body, dict) and "error" in body:
        code = body["error"].get("code") if isinstance(body["error"], dict) else None
        if code not in contract.error_codes:
            raise _fail(contract, operation_id, f"error code {code!r} is outside the documented enum")
        if body.get("request_id") != response.headers["X-Request-ID"]:
            raise _fail(contract, operation_id, "body request_id differs from the X-Request-ID header")


def assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None:
    contract = load_contract()
    spec = contract.operations.get(operation_id)
    if spec is None or spec.event_schema is None:
        raise _fail(contract, operation_id, "not a documented event-stream operation")
    schema = {"$ref": f"{CONTRACT_URI}#/components/schemas/{spec.event_schema}"}
    validator = Draft202012Validator(schema, registry=contract.registry, format_checker=_FORMATS)
    for frame in frames:
        payload = json.loads(frame.data)
        for error in validator.iter_errors(payload):
            where = "/".join(str(part) for part in error.absolute_path) or "(event)"
            raise _fail(
                contract, operation_id, f"event breaks {spec.event_schema} at {where}: {error.message[:200]}"
            )
        if frame.id is not None and str(payload.get("event_id")) != frame.id:
            raise _fail(contract, operation_id, "frame id differs from the event_id in its data")


def operations_documenting(status: str) -> frozenset[str]:
    return frozenset(op for op, spec in load_contract().operations.items() if status in spec.responses)


def operations_documenting_code(status: str, code: str) -> frozenset[str]:
    """Operations documenting `status` whose response carries an example with `error.code == code`."""
    document = load_document()
    found: set[str] = set()
    for path, item in document["paths"].items():
        for method in _METHODS:
            operation = item.get(method)
            if not isinstance(operation, dict) or "operationId" not in operation:
                continue
            raw = operation["responses"].get(status) or operation["responses"].get(int(status))
            if raw is None:
                continue
            response, _ = _resolve_response(
                document, raw, f"/paths/{_escape(path)}/{method}/responses/{status}"
            )
            media = (response.get("content") or {}).get("application/json") or {}
            examples = media.get("examples") or {}
            for example in examples.values():
                value = example.get("value") if isinstance(example, dict) else None
                if isinstance(value, dict) and (value.get("error") or {}).get("code") == code:
                    found.add(operation["operationId"])
    return frozenset(found)
