"""AEA-02 AC-20: staff-surface constants equal staff.md section 1 and the OpenAPI enum."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from meridian.domain.staff import CUSTOMER_SPEAKER_NAME, ROLE_ACTIONS, StaffRole, actor_for

OPENAPI = Path(__file__).resolve().parents[3] / "docs/ux/03-structure/ui-contracts.openapi.yaml"


def test_role_actions_and_customer_speaker_match_staff_md() -> None:
    loaded: Any = yaml.load(OPENAPI.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)  # noqa: S506  read-only plain-string load
    enum = set(
        loaded["components"]["schemas"]["CaseSummary"]["properties"]["allowed_actions"]["items"]["enum"]
    )

    owner = ROLE_ACTIONS[StaffRole.OWNER]
    supervisor = ROLE_ACTIONS[StaffRole.SUPERVISOR]
    representative = ROLE_ACTIONS[StaffRole.REPRESENTATIVE]
    print("owner:", sorted(owner))
    print("supervisor:", sorted(supervisor))
    print("representative:", sorted(representative))

    assert owner == frozenset()
    assert supervisor == {
        "claim",
        "release",
        "start",
        "wait",
        "resolve",
        "close_unresolved",
        "assign",
        "change_priority",
        "flag",
    }
    assert representative == enum - {"assign", "change_priority"}
    for actions in (owner, supervisor, representative):
        assert actions <= enum
    assert CUSTOMER_SPEAKER_NAME == "Customer"
    assert actor_for(StaffRole.SUPERVISOR).owns(StaffRole.SUPERVISOR)
    assert not actor_for(StaffRole.SUPERVISOR).owns(StaffRole.REPRESENTATIVE)
    assert not actor_for(StaffRole.SUPERVISOR).owns(None)
