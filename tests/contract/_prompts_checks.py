"""AEA-60 helper: compare what each prompt offers the model with what its consumer accepts (plan step 3).

Every helper raises `Drift` with a message naming role, field and value, never customer text. The guard at the end
records any open of a held-out path and any socket event while it is active (AC-12).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import typing
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel

from meridian.agent.prompts.reply import LABEL_SETTLED, LABEL_THIS_TURN, trimmed_schema
from meridian.agent.specialists.specs import REPORT_FACTS_TOOL, SPECS
from meridian.agent.tools.dispatch import ToolDispatcher, ToolRegistry
from meridian.domain.common import HandoffReason, LLMFacing
from meridian.domain.tools import SpecialistTask, ToolCallScope
from meridian.domain.turn import ResponderDraft
from meridian.ports.models import ChoiceRequest, StructuredRequest, ToolStepRequest

REPO_ROOT = Path(__file__).resolve().parents[2]


class Drift(AssertionError):
    """A prompt and its consumer disagree. The message names role, field and value, never message text."""


# --- vocabulary ---------------------------------------------------------------------------------------------------

# HandoffReason values only code may set (DO-4 section 7; CAS-16 option A, D-14).
CODE_ONLY: frozenset[str] = frozenset(
    {
        "safety",
        "danger",
        "burning_unclear",
        "customer_requested_person",
        "legal_or_chargeback",
        "commercial",
        "fee_bearing_change",
        "identity_unverified",
        "ai_failure",
        "burning_ruled_out",
    }
)
assert CODE_ONLY <= {r.value for r in HandoffReason}, sorted(CODE_ONLY - {r.value for r in HandoffReason})
FORBIDDEN_FIELDS: frozenset[str] = frozenset(
    {"priority", "case_ref", "case_reference", "reference", "promise", "promise_text", "customer_id"}
)
# The classifier's danger_level feeds DangerAssessment.label (raise-only, R-47), never HandoffReason (clarification C-1).
EXEMPT: frozenset[tuple[str, str]] = frozenset({("classifier", "danger_level")})


# --- schema helpers -----------------------------------------------------------------------------------------------


def literal_values(model: type[BaseModel], name: str) -> frozenset[str]:
    return frozenset(typing.get_args(model.model_fields[name].annotation))


def property_names(schema: object) -> set[str]:
    names: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                names.update(str(n) for n in value)
            names |= property_names(value)
    elif isinstance(schema, list):
        for item in schema:
            names |= property_names(item)
    return names


def enum_values(schema: object) -> set[str]:
    values: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "enum" and isinstance(value, list):
                values.update(str(v) for v in value)
            values |= enum_values(value)
    elif isinstance(schema, list):
        for item in schema:
            values |= enum_values(item)
    return values


def json_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            keys.add(str(k))
            keys |= json_keys(v)
    elif isinstance(value, list):
        for item in value:
            keys |= json_keys(item)
    return keys


_NO_RECURSE = frozenset({"default", "examples", "const", "enum"})


def _strip(node: Any) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key == "title" and isinstance(value, str):
                continue
            if key in ("properties", "$defs") and isinstance(value, dict):
                out[key] = {name: _strip(sub) for name, sub in value.items()}
            elif key in _NO_RECURSE:
                out[key] = value
            else:
                out[key] = _strip(value)
        return out
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def trimmed(args_model: type[LLMFacing]) -> dict[str, Any]:
    """An independent copy of the title-stripping rule (comparing the dispatcher with itself proves nothing)."""
    result = _strip(args_model.model_json_schema())
    assert isinstance(result, dict)
    return result


# --- routing ------------------------------------------------------------------------------------------------------


def check_choice_fields(
    role: str,
    request: ChoiceRequest,
    consumer: type[BaseModel],
    *,
    fields: Mapping[str, str] | None = None,
    consumer_name: str | None = None,
    code_only: frozenset[str] = frozenset(),
) -> None:
    """Field names and option keys of `request` against `consumer`, both directions, at most 255 characters each."""
    sent = {f.name: f for f in request.fields}
    mapping = dict(fields) if fields is not None else {name: name for name in consumer.model_fields}
    if fields is None:
        for name in sent:
            if name not in consumer.model_fields:
                raise Drift(f"{role} sends field '{name}'; {consumer.__name__} has no such field")
        for name in consumer.model_fields:
            if name not in sent:
                raise Drift(f"{role} does not send field '{name}'; {consumer.__name__} has it")
    for name, target in mapping.items():
        if name not in sent:
            raise Drift(f"{role} does not send field '{name}'; {consumer.__name__} has it")
        label = consumer_name or f"{consumer.__name__}.{target}"
        accepted = literal_values(consumer, target)
        offered = set(sent[name].options)
        for value in sorted(offered - accepted):
            raise Drift(f"{role}.{name} offers '{value}'; {label} does not accept it")
        for value in sorted(accepted - offered - code_only):
            raise Drift(f"{role}.{name} does not offer '{value}'; {label} accepts it")
        for key in offered:
            if len(key) > 255:
                raise Drift(f"{role}.{name} offers an option key longer than 255 characters")


def check_quoted_keys(role: str, request: ChoiceRequest) -> None:
    """Every option key the wording quotes must exist in the request's own options."""
    options = {key for f in request.fields for key in f.options}
    texts = [request.system, *(f.instructions for f in request.fields)]
    for text in texts:
        for key in re.findall(r'"([a-z_]+)"', text):
            if key not in options:
                raise Drift(f"{role} wording quotes option '{key}'; no field of the request offers it")


# --- specialists --------------------------------------------------------------------------------------------------


def check_specialist_request(
    kind: str,
    request: ToolStepRequest,
    registry: ToolRegistry,
    dispatcher: ToolDispatcher,
    task: SpecialistTask,
) -> None:
    spec = SPECS[kind]  # type: ignore[index]
    names = [t.name for t in request.tools]
    expected = [s.name for s in dispatcher.schemas(spec.tool_kinds)] + [REPORT_FACTS_TOOL]
    if names != expected:
        raise Drift(f"specialist.{kind} sends tools {names}; the registry offers {expected}")
    for tool in request.tools:
        if tool.name == REPORT_FACTS_TOOL:
            continue
        defn = registry.get(tool.name)
        if not re.fullmatch(r"[a-z_]{1,64}", tool.name):
            raise Drift(f"specialist.{kind} tool '{tool.name}' does not match the name pattern")
        if defn is None:
            raise Drift(f"specialist.{kind} sends tool '{tool.name}'; the registry has no such tool")
        if defn.kind not in spec.tool_kinds:
            raise Drift(f"specialist.{kind} sends tool '{tool.name}' of kind '{defn.kind.value}'")
        if tool.strict is not True:
            raise Drift(f"specialist.{kind}.{tool.name} is not strict")
        schema = dict(tool.input_schema)
        if schema != trimmed(defn.args_model):
            raise Drift(f"specialist.{kind}.{tool.name} schema differs from the trimmed args_model schema")
        if set(cast("dict[str, Any]", schema.get("properties", {}))) != set(defn.args_model.model_fields):
            raise Drift(f"specialist.{kind}.{tool.name} properties differ from its args_model fields")
        if schema.get("additionalProperties") is not False:
            raise Drift(f"specialist.{kind}.{tool.name} allows additional properties")
        for name in sorted(property_names(schema) & set(ToolCallScope.model_fields)):
            raise Drift(f"specialist.{kind}.{tool.name} offers scope field '{name}'")
    if registry.get(REPORT_FACTS_TOOL) is not None:
        raise Drift(f"specialist.{kind} registry holds a tool named '{REPORT_FACTS_TOOL}'")
    try:
        registry.check_covers(spec.tool_kinds)
    except ValueError as exc:
        raise Drift(f"specialist.{kind} kinds are not covered by the registry: {exc}") from exc
    report = next(t for t in request.tools if t.name == REPORT_FACTS_TOOL)
    if dict(report.input_schema) != spec.report_model.model_json_schema():
        raise Drift(f"specialist.{kind}.{REPORT_FACTS_TOOL} schema differs from {spec.report_model.__name__}")
    schemas = [dict(t.input_schema) for t in request.tools]
    allowed = (
        set(names)
        | {n for s in schemas for n in property_names(s)}
        | {v for s in schemas for v in enum_values(s)}
        | json_keys(task.slice.model_dump(mode="json"))
    )
    text = request.system_prefix + "\n" + request.system_dynamic
    for token in re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", text):
        if token not in allowed:
            raise Drift(f"specialist.{kind} wording names '{token}'; no tool sent with it")


# --- reply --------------------------------------------------------------------------------------------------------

_DRAFT_SCHEMA = {
    "additionalProperties": False,
    "properties": {"text": {"maxLength": 1200, "minLength": 1, "type": "string"}},
    "required": ["text"],
    "type": "object",
}


def check_responder_request(request: StructuredRequest[Any]) -> None:
    if request.output_model is not ResponderDraft:
        for name in sorted(property_names(request.output_model.model_json_schema()) - {"text"}):
            raise Drift(f"responder.output_model offers '{name}'; ResponderDraft does not accept it")
        raise Drift("responder.output_model is not ResponderDraft")
    if json.loads(trimmed_schema(ResponderDraft)) != _DRAFT_SCHEMA:
        raise Drift("responder.output_model schema differs from the signed draft schema")
    if trimmed_schema(ResponderDraft) not in request.system_prefix:
        raise Drift("responder.system_prefix does not carry the trimmed draft schema")
    for label in (LABEL_THIS_TURN, LABEL_SETTLED):
        if label not in request.system_dynamic:
            raise Drift(f"responder.system_dynamic lacks the block '{label}'")
    for name in sorted(property_names(request.output_model.model_json_schema()) & FORBIDDEN_FIELDS):
        raise Drift(f"responder.output_model offers '{name}'; the model may not set it")


_BRIEF_LINE = re.compile(r"^\[message (\d+)\] (.*)$")


def parse_brief_lines(user: str) -> dict[int, str]:
    rendered: dict[int, str] = {}
    for line in user.split("\n"):
        match = _BRIEF_LINE.match(line)
        if match:
            rendered[int(match.group(1))] = match.group(2)
    return rendered


def check_brief_ids(rendered: Mapping[int, str], shown: Mapping[int, str], customer_ids: set[int]) -> None:
    for mid in rendered:
        if mid not in customer_ids:
            raise Drift(f"brief.shown offers message {mid} which is not a customer message of this thread")
    if dict(rendered) != dict(shown):
        raise Drift("brief.shown differs from the messages check_quotes compares quotes against")


# --- inventory ----------------------------------------------------------------------------------------------------


def missing_cases(names: Iterable[str], renderers: Mapping[str, object]) -> None:
    for name in names:
        if name == "specialist":
            if all(f"specialist:{kind}" in renderers for kind in SPECS):
                continue
        elif name in renderers:
            continue
        raise Drift(f"{name} has no rendered case")


# --- held-out and socket guard (AC-12) -------------------------------------------------------------------------------

HELD_OUT_PREFIXES: list[str] = [
    str(REPO_ROOT / "eval" / "cases" / "heldout"),
    str(Path.home() / ".meridian-sealed"),
]


@dataclass
class Guard:
    active: bool = False
    opens: list[str] = field(default_factory=list)
    connects: list[str] = field(default_factory=list)


GUARD = Guard()
_installed = False


def _hook(event: str, args: tuple[object, ...]) -> None:
    if not GUARD.active:
        return
    with contextlib.suppress(Exception):  # an audit hook must never raise
        if event == "open" and args and isinstance(args[0], str | bytes | os.PathLike):
            path = os.path.abspath(os.fsdecode(args[0]))
            if any(path.startswith(prefix) for prefix in HELD_OUT_PREFIXES):
                GUARD.opens.append(path)
        elif event in ("socket.connect", "socket.getaddrinfo"):
            GUARD.connects.append(event)


def install_guard() -> None:
    """Audit hooks cannot be removed, so the hook stays inert unless GUARD.active."""
    global _installed
    if not _installed:
        sys.addaudithook(_hook)
        _installed = True
