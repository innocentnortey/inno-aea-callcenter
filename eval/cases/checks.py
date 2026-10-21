"""Pure validation helpers for the eval case files (AEA-06). Standard library and eval.cases.models only."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Final

from eval.cases.models import CaseKey, CaseScript

SYNTHETIC_KINDS: Final[tuple[str, ...]] = (
    "safety phrasing",
    "danger comfort",
    "no-danger comfort",
    "person request",
    "failure signal",
    "identity edge",
    "prompt injection",
)
FORM_FIELDS: Final = frozenset({"name", "phone", "customer_id", "invoice_number", "zip_or_city"})
CONTACT_FIELDS: Final = frozenset({"name", "phone"})  # must always be "$seed:<field>"
SEED_TOKEN: Final = re.compile(r"^\$seed:(name|phone|customer_id|invoice_number|zip_or_city)$")
CASE_ID: Final = re.compile(r"^(?:WP-[1-8]|WP-4F|DANGER|NODANGER|T-CALL-\d{8}-\d{4}|S-\d{1,2}|P-\d{1,3})$")
QUERY_ID: Final = re.compile(r"^R-\d{1,2}$")
FLAG_REF: Final = re.compile(r"^flag:flg-\d+ trace:[0-9a-f]{32}$")
FINDING_REF: Final = re.compile(r"^finding:FT-\d+ trace:[0-9a-f]{32}$")
DEMO_CLOCK: Final = "2026-10-16T10:00:00-05:00"
CUSTOMER_ID: Final = re.compile(r"^MHC-\d{5}$")

# Source grammar: one or more tokens joined by "; ". Each token is exactly one of:
REQ_TOKEN: Final = re.compile(r"^R-\d{1,2}$")  # PRD requirement
DECISION_TOKEN: Final = re.compile(
    r"^(?:D\d{1,2}|DEC-\d{1,2}|OD-\d{1,2}|HP-\d|DAT-\d{1,2}|EVQ-\d|CAS-\d{1,2}|Q-\d{3})$"
)
SCREEN_TOKEN: Final = re.compile(r"^SCREEN_SPECS SCR-(\d{1,2})$")
DB_TOKEN: Final = re.compile(
    r"^db:(customers|appointments|appointment_slots|invoices|technicians)/([A-Za-z0-9-]+)$"
)
SCHEMA_TOKEN: Final = "SCHEMA.md"  # noqa: S105 - a source label, not a password
KB_TOKEN: Final = re.compile(
    r"^[a-z_]+/[A-Za-z0-9_.-]+\.(?:md|txt|pdf|csv|png)$"
)  # path under knowledge_base/
FORBIDDEN_SOURCE: Final = re.compile(r"CALL-\d{8}-\d{4}|transcript|trace", re.IGNORECASE)


def source_problems(
    source: str,
    *,
    kb_status: Mapping[str, str],
    db_has: Callable[[str, str], bool],
) -> list[str]:
    """Problems with one item source; empty means every token traces to a current KB file, DB row or decision."""
    if not source.strip():
        return ["empty source"]
    problems: list[str] = []
    for token in source.split("; "):
        if FORBIDDEN_SOURCE.search(token):
            problems.append("transcript or trace source")
        elif (
            REQ_TOKEN.match(token)
            or DECISION_TOKEN.match(token)
            or SCREEN_TOKEN.match(token)
            or token == SCHEMA_TOKEN
        ):
            continue
        elif (db := DB_TOKEN.match(token)) is not None:
            if not db_has(db.group(1), db.group(2)):
                problems.append(f"no DB row: {token}")
        elif KB_TOKEN.match(token):
            if kb_status.get(token) != "current":
                problems.append(f"not a current KB file: {token}")
        else:
            problems.append(f"unknown source token: {token}")
    return problems


def screen_specs_sections(text: str) -> dict[int, str]:
    """Split SCREEN_SPECS.md at lines starting '### SCR-<n> ·'; section n runs to the next '### ' or '## ' line."""
    sections: dict[int, list[str]] = {}
    current: int | None = None
    for line in text.splitlines():
        head = re.match(r"^### SCR-(\d+) ·", line)
        if head:
            current = int(head.group(1))
            sections[current] = []
        elif line.startswith("### ") or line.startswith("## "):
            current = None
        elif current is not None:
            sections[current].append(line)
    return {n: "\n".join(lines) for n, lines in sections.items()}


def turn_problems(script: CaseScript) -> list[str]:
    """Problems with a script's turns and seeded customer (no contact literal, no code)."""
    problems: list[str] = []
    uses_seed = False
    for i, turn in enumerate(script.turns):
        where = f"turns[{i}]"
        if turn.kind == "text":
            if not turn.text:
                problems.append(f"{where}: text turn needs text")
            if turn.choice is not None or turn.form is not None:
                problems.append(f"{where}: text turn carries choice or form")
        elif turn.kind == "choice":
            if not turn.choice:
                problems.append(f"{where}: choice turn needs choice")
            if turn.text is not None or turn.form is not None:
                problems.append(f"{where}: choice turn carries text or form")
        elif turn.kind == "form":
            if not turn.form:
                problems.append(f"{where}: form turn needs form")
            if turn.text is not None or turn.choice is not None:
                problems.append(f"{where}: form turn carries text or choice")
            for field, value in (turn.form or {}).items():
                if field not in FORM_FIELDS:
                    problems.append(f"{where}: unknown form field {field}")
                token = SEED_TOKEN.match(value)
                if token is not None:
                    uses_seed = True
                    if token.group(1) != field:
                        problems.append(f"{where}: {field} holds the token of another field")
                elif field in CONTACT_FIELDS:
                    problems.append(f"{where}: {field} must be a $seed: token")
        elif turn.text is not None or turn.choice is not None or turn.form is not None:
            problems.append(f"{where}: {turn.kind} turn carries no payload")
    if uses_seed and (script.seeded_customer is None or not CUSTOMER_ID.match(script.seeded_customer)):
        problems.append("seeded_customer: $seed: tokens need a customer id")
    if script.seeded_customer is not None and not CUSTOMER_ID.match(script.seeded_customer):
        problems.append("seeded_customer: must be a customer id (MHC-nnnnn)")
    return problems


def promoted_case_problems(script: CaseScript, key: CaseKey | None) -> list[str]:
    """Review rules for a promoted-trace case (EV-18, EV-12); empty for every other provenance."""
    if script.provenance != "promoted-trace":
        return []
    problems: list[str] = []
    is_finding = FINDING_REF.match(script.source_ref) is not None
    if not (FLAG_REF.match(script.source_ref) or is_finding):
        problems.append("source_ref: needs flag:flg-<n> trace:<32 hex> or finding:FT-<n> trace:<32 hex>")
    if script.labelled_by != "Innocent":
        problems.append("labelled_by: must be Innocent")
    if is_finding and script.split != "dev":
        problems.append("split: a finding-promoted case is dev only")
    if key is not None:
        lists = (
            ("must_do", key.must_do),
            ("must_say", key.must_say),
            ("must_not_say", key.must_not_say),
            ("judge_items", key.judge_items),
        )
        for name, items in lists:
            for i, item in enumerate(items):
                if FORBIDDEN_SOURCE.search(item.source):
                    problems.append(f"source: {name}[{i}] cites a transcript or trace")
    return problems


def script_problems(script: CaseScript) -> list[str]:
    """Problems with one case script."""
    problems: list[str] = []
    if not CASE_ID.match(script.case_id):
        problems.append(f"case_id: {script.case_id} has no valid form")
    if script.clock is None or script.clock.isoformat() != DEMO_CLOCK:
        problems.append(f"clock: must be {DEMO_CLOCK}")
    if script.synthetic in {"partly", "yes"} and not script.synthetic_assumption:
        problems.append("synthetic_assumption: required when synthetic is partly or yes")
    if script.synthetic == "yes" and not (script.varied_dimension and script.synthetic_source_case):
        problems.append("varied_dimension, synthetic_source_case: required when synthetic is yes")
    if script.provenance == "synthetic" and not any(
        (script.varied_dimension or "").startswith(f"{kind}: ") for kind in SYNTHETIC_KINDS
    ):
        problems.append("varied_dimension: must start with a synthetic kind label and ': '")
    return problems + turn_problems(script) + promoted_case_problems(script, None)


def key_problems(key: CaseKey) -> list[str]:
    """Problems with one answer key."""
    problems: list[str] = []
    if not CASE_ID.match(key.case_id):
        problems.append(f"case_id: {key.case_id} has no valid form")
    if not key.in_scope and key.topic is not None:
        problems.append("topic: an out-of-scope case has no topic")
    if key.unscored is not None and not (len(key.unscored) >= 20 and key.unscored.endswith("?")):
        problems.append("unscored: must be an open question of at least 20 characters ending in '?'")
    if not key.guards:
        problems.append("guards: must not be empty")
    return problems


def form_tokens_in(script: CaseScript) -> set[str]:
    """Every $seed: token a script's form turns use."""
    return {v for t in script.turns for v in (t.form or {}).values() if SEED_TOKEN.match(v)}
