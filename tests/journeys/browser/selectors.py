"""The one selector module (AEA-58 AC-16): logical keys, contract rows, locator builders, dev-layer markers.

Rows come only from the UX session's selector contract (SELECTORS_SOURCE). Until that file exists no row is
transcribed, and every on-screen step reports blocked-on UX session. Never invent a row, use copy text the file does
not give, or read apps/web/src to fill a gap.

Parametric keys (PARAMETRIC_KEYS, AEA-58-F1): the row holds exactly one {value} placeholder (in value, or in name for
a role row); tests reach it only through locate_by, which fills it with an id, reference or number matching
PARAM_VALUE.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal

from tests.journeys.support.steps import Missing

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

SELECTORS_SOURCE: Final = "docs/plans/ux-join/selectors.md"
SELECTORS_REVISION: Final[str | None] = None  # short SHA of the last commit touching SELECTORS_SOURCE
SelectorKind = Literal["css", "role", "label"]


@dataclass(frozen=True)
class SelectorRow:
    key: str
    kind: SelectorKind
    value: str  # css: the selector text; role: the ARIA role; label: the accessible label text
    name: str | None  # role only: the exact accessible name
    row: str  # the row's id or heading in selectors.md, quoted exactly


SELECTOR_KEYS: Mapping[str, str] = MappingProxyType(
    {
        "screen.scr1": "SCR-1 root is drawn",
        "screen.scr12": "SCR-12 root is drawn",
        "login.username": "SCR-12 username input",
        "login.password": "SCR-12 password input",
        "login.submit": "SCR-12 'Sign in' button",
        "login.show_password": "SCR-12 'Show password' checkbox",
        "login.message.refused": "SCR-12 refusal line ([data-login-message=refused])",
        "login.message.rate_limited": "SCR-12 throttle line ([data-login-message=rate-limited])",
        "chat.ready": "SCR-1 chat ready to type ([data-chat-state=ready])",
        "chat.entry": "each thread entry, in order ([data-entry])",
        "chat.entry.customer": "a customer entry ([data-speaker=customer])",
        "chat.entry.assistant": "an assistant entry ([data-speaker=assistant])",
        "chat.block.text": "a text reply block inside an entry ([data-block-type=text])",
        "chat.composer": "SCR-1 message box",
        "chat.send": "SCR-1 'Send' button",
        "shell.sign_out": "the shared header's 'Sign out' control",
        "screen.scr2": "SCR-2 root is drawn",
        "screen.scr4": "SCR-4 root is drawn",
        "screen.scr5": "SCR-5 root is drawn",
        "screen.scr6": "SCR-6 root is drawn",
        "login.message.expired": "SCR-12 expired-session line",
        "chat.source": "a cited source chip naming its document",
        "chat.source.toggle": "the control that opens a source chip",
        "chat.source.excerpt": "the quoted passage an open source chip shows",
        "chat.block.locate_prompt": "a locate reply block ([data-block-type])",
        "chat.block.code_prompt": "a code reply block ([data-block-type])",
        "chat.block.account_card": "an account card reply block ([data-block-type])",
        "chat.block.slot_card": "a slot card reply block ([data-block-type])",
        "chat.block.confirmation": "a confirmation reply block ([data-block-type])",
        "chat.block.handoff": "a handoff reply block ([data-block-type])",
        "card.locate.name": "locate card name input",
        "card.locate.phone": "locate card phone input",
        "card.locate.submit": "locate card submit control",
        "card.code.input": "code card input",
        "card.code.submit": "code card submit control",
        "card.slot.window_by_id": "one window in a slot card, by slot id (parametric)",
        "card.slot.continue": "slot card 'Continue with this window' control",
        "settled.visit": "'What's settled' visit row ([data-visit-status])",
        "settled.request": "'What's settled' request row ([data-request-ref])",
        "inbox.message.active": "SCR-2 newest active message ([data-inbox-status=active])",
        "inbox.code": "SCR-2 code, readable as text",
        "shell.role.customer": "'Acting as' radio: Customer",
        "shell.role.representative": "'Acting as' radio: Representative",
        "shell.role.supervisor": "'Acting as' radio: Supervisor",
        "shell.role.owner": "'Acting as' radio: Owner",
        "shell.header_name": "the shell's signed-in display name",
        "role.panel": "SCR-4 / staff role panel ([data-testid=role-panel])",
        "role.panel.wrong_role": "role panel with reason wrong_role ([data-reason])",
        "role.panel.role_reset": "role panel with reason role_reset ([data-reason])",
        "queue.row": "every SCR-5 queue row, in order",
        "queue.row_by_ref": "the SCR-5 queue row of one case reference (parametric)",
        "case.root": "SCR-6 case loaded ([data-testid=case])",
        "case.owner": "SCR-6 owner line (case-owner)",
        "case.promise": "SCR-6 promise card ([data-promise-status])",
        "case.promise.open": "SCR-6 promise card with status open",
        "brief.section_by_number": "brief section #brief-<n> (parametric)",
        "brief.heading": "a brief section's heading",
        "brief.item.tag": "the 'Customer says · not checked' tag on a brief item",
        "case.sources_tab": "SCR-6 Sources tab",
        "case.source_by_id": "SCR-6 source #src-<source_id> (parametric)",
        "demo.reset": "SCR-3 reset control",
        "demo.reset_result": "SCR-3 reset result ([data-reset-result])",
    }
)
CONTRACT_ROWS: Mapping[str, SelectorRow] = MappingProxyType({})  # filled only from SELECTORS_SOURCE

# Dev-layer absence markers: not UI selectors; used only with page.evaluate to prove absence (AC-1).
DEV_LAYER_GLOBAL: Final = "__MHC_DEV_LAYER__"  # apps/web/src/dev/install.ts:17
DEV_PANEL_ROOT_ID: Final = "mhc-dev-panel-root"  # apps/web/src/dev/install.ts:48

UX_OWNER: Final = "UX session"

PLACEHOLDER: Final = "{value}"
PARAMETRIC_KEYS: frozenset[str] = frozenset(
    {"card.slot.window_by_id", "queue.row_by_ref", "brief.section_by_number", "case.source_by_id"}
)
PARAM_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")  # ids, references, section numbers


def missing_selectors(keys: Sequence[str]) -> tuple[Missing, ...]:
    found: list[Missing] = []
    for key in keys:
        if key not in SELECTOR_KEYS:
            raise KeyError(f"unknown selector key {key!r}: add it to SELECTOR_KEYS")
        if key not in CONTRACT_ROWS:
            found.append(Missing(f"UX selector {key} not in {SELECTORS_SOURCE}", UX_OWNER))
    return tuple(found)


def placeholder_count(row: SelectorRow) -> int:
    return row.value.count(PLACEHOLDER) + (row.name or "").count(PLACEHOLDER)


def fill_row(row: SelectorRow, value: str) -> SelectorRow:
    """A parametric row with its one {value} placeholder filled (in `value`, or in `name` for a role row)."""
    if not PARAM_VALUE.fullmatch(value):
        raise ValueError(f"bad selector value {value!r}: expected {PARAM_VALUE.pattern}")
    if placeholder_count(row) != 1:
        raise ValueError(f"row for {row.key!r} must hold exactly one {PLACEHOLDER}")
    name = None if row.name is None else row.name.replace(PLACEHOLDER, value)
    return replace(row, value=row.value.replace(PLACEHOLDER, value), name=name)


def _row(key: str, *, parametric: bool) -> SelectorRow:
    if key not in SELECTOR_KEYS:
        raise KeyError(f"unknown selector key {key!r}: add it to SELECTOR_KEYS")
    if key in PARAMETRIC_KEYS and not parametric:
        raise ValueError(f"{key!r} is parametric: use locate_by")
    if parametric and key not in PARAMETRIC_KEYS:
        raise ValueError(f"{key!r} takes no value: use locate or locate_in")
    return CONTRACT_ROWS[key]


def _build(target: Page | Locator, row: SelectorRow) -> Locator:
    if row.kind == "css":
        return target.locator(row.value)
    if row.kind == "role":
        return target.get_by_role(row.value, name=row.name, exact=True)  # type: ignore[arg-type]
    return target.get_by_label(row.value, exact=True)


def locate(page: Page, key: str) -> Locator:
    return _build(page, _row(key, parametric=False))


def locate_in(parent: Locator, key: str) -> Locator:
    return _build(parent, _row(key, parametric=False))


def locate_by(target: Page | Locator, key: str, value: str) -> Locator:
    """A parametric key (PARAMETRIC_KEYS) with its value filled (AEA-58-F1 A-2)."""
    return _build(target, fill_row(_row(key, parametric=True), value))
