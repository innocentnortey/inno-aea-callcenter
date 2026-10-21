"""Case files for AEA-59's server runner: loading, the shared vocabulary, static checks and completeness.

Each route ticket writes one `tests/contract/cases/<route>.py` holding `ROUTE_FILE` and `CASES` (keyed by operationId).
This module reads them (never writes them), maps each file's words to canonical steps, and proves every operationId in the
signed OpenAPI has exactly one case. The format is documented in `tests/contract/cases/README.md`.
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from tests.api.events_support import PAYLOADS
from tests.api.openapi_check import load_contract
from tests.contract.openapi_variants import operation_node, request_examples

CASES_DIR: Final = Path(__file__).resolve().parent / "cases"
README_PATH: Final = CASES_DIR / "README.md"


@dataclass(frozen=True)
class CaseFile:
    stem: str
    route_file: object
    cases: Mapping[str, Mapping[str, Any]]


def load_case_files() -> list[CaseFile]:
    files: list[CaseFile] = []
    for path in sorted(CASES_DIR.glob("*.py")):
        if path.stem == "__init__" or path.stem.startswith("_"):
            continue
        module = importlib.import_module(f"tests.contract.cases.{path.stem}")
        files.append(
            CaseFile(
                stem=path.stem,
                route_file=getattr(module, "ROUTE_FILE", None),
                cases=getattr(module, "CASES", {}),
            )
        )
    return files


# -- which route file owns which operation (api-con-mapping.md) -----------------------------------------------
ROUTE_FILE_BY_CON: Final[Mapping[str, str]] = MappingProxyType(
    {
        "CON-1": "chat", "CON-2": "chat", "CON-3": "events", "CON-4": "handoff", "CON-5": "handoff",
        "CON-6": "demo", "CON-7": "demo", "CON-8": "demo", "CON-9": "demo", "CON-10": "staff_session",
        "CON-11": "staff_cases", "CON-12": "staff_cases", "CON-13": "staff_cases", "CON-14": "staff_live",
        "CON-15": "staff_cases", "CON-16": "staff_cases", "CON-17": "staff_cases", "CON-18": "reads",
        "CON-19": "reads", "CON-20": "reads", "CON-21": "staff_live", "CON-22": "auth",
    }
)  # fmt: skip
ROUTE_FILE_OVERRIDES: Final[Mapping[tuple[str, str], str]] = MappingProxyType(
    {("CON-8", "post"): "staff_clock"}
)


def expected_route_file(operation_id: str) -> str:
    spec = load_contract().operations[operation_id]
    con = str(operation_node(operation_id).get("x-con", "?"))
    return ROUTE_FILE_OVERRIDES.get(
        (con, spec.method), ROUTE_FILE_BY_CON.get(con, f"<no route file for {con}>")
    )


def is_public(operation_id: str) -> bool:
    return bool(operation_node(operation_id).get("security") == [])


def staff_role_for(operation_id: str) -> str | None:
    """None when a customer may call the operation, else the first role its `x-roles` allows."""
    raw = operation_node(operation_id).get("x-roles")
    roles = [str(e).split()[0] for e in raw] if raw else ["customer", "representative", "supervisor", "owner"]
    return None if "customer" in roles else roles[0]


# -- vocabulary -----------------------------------------------------------------------------------------------
PRECONDITIONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "login": "login",
        "thread": "thread", "started_thread": "thread", "start_thread": "thread",
        "open_case": "open_case",
        "verified": "verified",
        "ended": "ended",
        "unknown": "unknown",
        "role:customer": "role:customer", "role:representative": "role:representative",
        "role:supervisor": "role:supervisor", "role:owner": "role:owner",
        "as_customer": "role:customer", "as_representative": "role:representative",
        "as_supervisor": "role:supervisor", "as_owner": "role:owner",
    }
)  # fmt: skip
SETUPS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "login_rejects_exhausted": "login_rejects_exhausted",
        "reset_held": "reset_held", "reset_gate_held": "reset_held",
        "other_session_thread": "other_session_thread",
        "ended_thread": "ended",
    }
)  # fmt: skip
LOCAL_DRIVER_ONLY: Final[Mapping[str, str]] = MappingProxyType(
    {
        "handoff_fails": "needs a failing HandoffService double; proved by the route's local driver (mock-tested)",
        "turn_running": "needs a turn left running mid-request; proved by the route's local driver (mock-tested)",
        "live_case_claimed": "seeds a claimed live case; proved by the route's local driver (mock-tested)",
        "live_case_joined": "seeds a joined live case; proved by the route's local driver (mock-tested)",
        "live_case_unclaimed": "seeds an unclaimed live case; proved by the route's local driver (mock-tested)",
        "case_claimed_by_supervisor": "seeds a supervisor-owned case; proved by the route's local driver (mock-tested)",
        "case_events": "seeds case-stream events; proved by the route's local driver (mock-tested)",
        "rate_limited": "needs the rate limiter to refuse the request; proved by the route's local driver (mock-tested)",
    }
)
PATH_WORDS: Final = frozenset({"started", "unknown", "malformed", "other_session", "ended", "seeded_case"})
MALFORMED_THREAD_ID: Final = "thr_9d41"
ALLOWED_DRIVE_KEYS: Final = frozenset(
    {
        "name", "status", "code", "preconditions", "setup", "body", "path", "thread", "reference",
        "events", "last_event_id", "frames", "response_example", "reader_example",
    }
)  # fmt: skip
# "response_example" and "reader_example" are checked by the route's own driver; the runner ignores them.


@dataclass(frozen=True)
class Drive:
    operation_id: str
    file: str
    spec: Mapping[str, Any]

    @property
    def id(self) -> str:
        return f"{self.operation_id}/{self.spec.get('name', '?')}"

    @property
    def status(self) -> int:
        return int(self.spec["status"])


def all_drives(files: Sequence[CaseFile]) -> list[Drive]:
    drives: list[Drive] = []
    for case_file in files:
        for op_id, case in case_file.cases.items():
            drives.extend(
                Drive(op_id, case_file.stem, spec)
                for spec in case.get("drives", ())
                if isinstance(spec, dict)
            )
    return drives


def local_words(drive: Drive) -> list[str]:
    """Setup and precondition words of this drive that only the route's local driver can produce."""
    words = [str(w) for w in drive.spec.get("preconditions", ())]
    if "setup" in drive.spec:
        words.append(str(drive.spec["setup"]))
    return [w for w in words if w in LOCAL_DRIVER_ONLY]


def local_driver_reason(drive: Drive) -> str | None:
    found = local_words(drive)
    return LOCAL_DRIVER_ONLY[found[0]] if found else None


def _path_params(template: str) -> list[str]:
    return re.findall(r"\{(\w+)\}", template)


def check_cases_mapping(cases: Mapping[str, Mapping[str, Any]], where: str) -> list[str]:
    """One problem string per violation of the case format (prefix `where`, then `op/drive`)."""
    contract = load_contract()
    problems: list[str] = []
    if not isinstance(cases, dict):
        return [f"{where}: CASES is not a dict"]
    for op_id, case in cases.items():
        spec = contract.operations.get(op_id)
        if spec is None:
            problems.append(f"{where}: case for unknown operationId {op_id}")
            continue
        if case.get("public") is not is_public(op_id):
            problems.append(f"{where}: {op_id}: public must be {is_public(op_id)}")
        drives = case.get("drives")
        if (
            not isinstance(drives, (tuple, list))
            or not drives
            or not all(isinstance(d, dict) for d in drives)
        ):
            problems.append(f"{where}: {op_id}: drives must be a non-empty tuple of dicts")
            continue
        examples = request_examples(op_id)
        names: set[str] = set()
        success_examples: set[str] = set()
        has_success = False
        for d in drives:
            label = f"{where}: {op_id}/{d.get('name', '?')}"
            extra = set(d) - ALLOWED_DRIVE_KEYS
            if extra:
                problems.append(f"{label}: unknown drive keys {sorted(extra)}")
            name = d.get("name")
            if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+", name) or name in names:
                problems.append(f"{label}: name must be unique and match [a-z0-9_]+")
            names.add(str(name))
            status = d.get("status")
            if not isinstance(status, int) or str(status) not in spec.responses:
                problems.append(f"{label}: status {status!r} is not documented for {op_id}")
                continue
            if "code" in d and (d["code"] not in contract.error_codes or status < 400):
                problems.append(f"{label}: code {d['code']!r} is not an error code of an error status")
            pre = d.get("preconditions", ())
            if not isinstance(pre, (tuple, list)):
                problems.append(f"{label}: preconditions must be a tuple")
                pre = ()
            for word in pre:
                if word not in PRECONDITIONS and word not in LOCAL_DRIVER_ONLY:
                    problems.append(f"{label}: unknown precondition word {word!r}")
            if "setup" in d and d["setup"] not in SETUPS and d["setup"] not in LOCAL_DRIVER_ONLY:
                problems.append(f"{label}: unknown setup word {d['setup']!r}")
            body = d.get("body")
            if body is not None:
                if not isinstance(body, dict):
                    problems.append(f"{label}: body must be None or a dict")
                else:
                    kinds = [k for k in ("example", "raw", "text") if k in body]
                    if len(kinds) != 1:
                        problems.append(f"{label}: body needs exactly one of example, raw, text")
                    if "example" in body and body["example"] not in examples:
                        problems.append(f"{label}: unknown request example {body['example']!r}")
                    if "credentials" in body and (
                        "example" not in body or body["credentials"] not in ("configured", "wrong_password")
                    ):
                        problems.append(
                            f"{label}: credentials must be configured or wrong_password, with example"
                        )
                    if "turn_id" in body and (body["turn_id"] != "new" or "example" not in body):
                        problems.append(f"{label}: turn_id must be 'new', with example")
            path = d.get("path")
            params = _path_params(spec.path_template)
            if path is not None and (not isinstance(path, dict) or not set(path) <= set(params)):
                problems.append(f"{label}: path keys must be path parameters {params}")
            if "thread" in d and "thread_id" not in params:
                problems.append(f"{label}: thread is only for templates with {{thread_id}}")
            events = d.get("events")
            if events is not None:
                if op_id != "streamChatEvents" or not any(PRECONDITIONS.get(w) == "thread" for w in pre):
                    problems.append(f"{label}: events need streamChatEvents and a thread precondition")
                if not all(e in PAYLOADS for e in events):
                    problems.append(f"{label}: events must be keys of events_support.PAYLOADS")
                elif status == 200 and events and events[-1] not in ("chat_closed", "demo_reset"):
                    problems.append(f"{label}: the last seeded event must end the stream")
            last = d.get("last_event_id")
            if last is not None and not (isinstance(last, int) and not isinstance(last, bool) and last >= 1):
                # an int is a literal header value (staff_live seeds case events itself); the dict form indexes `events`
                count = len(events or ())
                if not (
                    isinstance(last, dict)
                    and set(last) == {"after_event"}
                    and 1 <= last["after_event"] <= count
                ):
                    problems.append(
                        f"{label}: last_event_id must be None, an int or {{'after_event': 1..{count}}}"
                    )
            frames = d.get("frames")
            if spec.event_schema and status == 200 and not (isinstance(frames, int) and frames >= 1):
                problems.append(f"{label}: an SSE success drive needs frames >= 1")
            if 200 <= status < 300:
                has_success = True
                if isinstance(body, dict) and "example" in body:
                    success_examples.add(str(body["example"]))
        if not has_success:
            problems.append(f"{where}: {op_id}: needs at least one 2xx drive")
        for example_name in examples:
            if example_name not in success_examples:
                problems.append(f"{where}: {op_id}: request example {example_name} has no success drive")
    return problems


def case_file_problems(files: Sequence[CaseFile]) -> list[str]:
    problems: list[str] = []
    owner: dict[str, str] = {}
    for case_file in files:
        where = f"cases/{case_file.stem}.py"
        if case_file.route_file != case_file.stem:
            problems.append(f"{where}: ROUTE_FILE is {case_file.route_file!r}, not {case_file.stem!r}")
        if not case_file.cases:
            problems.append(f"{where}: CASES is missing or empty")
        problems.extend(check_cases_mapping(case_file.cases, where))
        for op_id in case_file.cases:
            if op_id in owner:
                problems.append(f"{op_id}: appears in cases/{owner[op_id]}.py and {where}")
            owner[op_id] = case_file.stem
            if op_id in load_contract().operations and expected_route_file(op_id) != case_file.stem:
                problems.append(f"{where}: {op_id} belongs in cases/{expected_route_file(op_id)}.py")
    return problems


def missing_operations(found_ids: Iterable[str]) -> list[str]:
    missing = sorted(set(load_contract().operations) - set(found_ids))
    return [f"{op} → tests/contract/cases/{expected_route_file(op)}.py" for op in missing]


def completeness(files: Sequence[CaseFile]) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """(found ids per file stem, missing lines, unknown-id lines)."""
    found = {f.stem: list(f.cases) for f in files}
    known = set(load_contract().operations)
    all_ids = [op for ids in found.values() for op in ids]
    unknown = [f"cases/{stem}.py: {op}" for stem, ids in found.items() for op in ids if op not in known]
    return found, missing_operations(all_ids), unknown
