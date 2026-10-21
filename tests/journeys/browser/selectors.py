"""The one selector module (AEA-58 AC-16): logical keys, contract rows, locator builders, dev-layer markers.

Rows come only from the UX session's selector contract (SELECTORS_SOURCE). Until that file exists no row is
transcribed, and every on-screen step reports blocked-on UX session. Never invent a row, use copy text the file does
not give, or read apps/web/src to fill a gap.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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
    }
)
CONTRACT_ROWS: Mapping[str, SelectorRow] = MappingProxyType({})  # filled only from SELECTORS_SOURCE

# Dev-layer absence markers: not UI selectors; used only with page.evaluate to prove absence (AC-1).
DEV_LAYER_GLOBAL: Final = "__MHC_DEV_LAYER__"  # apps/web/src/dev/install.ts:17
DEV_PANEL_ROOT_ID: Final = "mhc-dev-panel-root"  # apps/web/src/dev/install.ts:48

UX_OWNER: Final = "UX session"


def missing_selectors(keys: Sequence[str]) -> tuple[Missing, ...]:
    found: list[Missing] = []
    for key in keys:
        if key not in SELECTOR_KEYS:
            raise KeyError(f"unknown selector key {key!r}: add it to SELECTOR_KEYS")
        if key not in CONTRACT_ROWS:
            found.append(Missing(f"UX selector {key} not in {SELECTORS_SOURCE}", UX_OWNER))
    return tuple(found)


def locate(page: Page, key: str) -> Locator:
    row = CONTRACT_ROWS[key]
    if row.kind == "css":
        return page.locator(row.value)
    if row.kind == "role":
        return page.get_by_role(row.value, name=row.name, exact=True)  # type: ignore[arg-type]
    return page.get_by_label(row.value, exact=True)


def locate_in(parent: Locator, key: str) -> Locator:
    row = CONTRACT_ROWS[key]
    if row.kind == "css":
        return parent.locator(row.value)
    if row.kind == "role":
        return parent.get_by_role(row.value, name=row.name, exact=True)  # type: ignore[arg-type]
    return parent.get_by_label(row.value, exact=True)
