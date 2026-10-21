"""The allowed_actions table of AEA-29 AC-18 (plan Appendix B), frozen with the tests.

Each ``TABLE`` row: ``(row, lifecycle, owner_role, live_state, staffing, representative, supervisor, owner)`` where the
last three are the expected ``allowed_actions`` lists in order. ``REPRESENTATIVE_EXAMPLES`` are copied from the signed
OpenAPI examples (getCase DEFAULT, WAITING, LIVE_JOINED and applyCaseAction CLAIMED).
"""

from __future__ import annotations

from meridian.domain.staff import StaffRole

REP = StaffRole.REPRESENTATIVE
SUP = StaffRole.SUPERVISOR

_REP_WORK = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"]
_SUP_ASSIGN = ["assign", "change_priority", "flag"]
_SUP_OWN = ["wait", "resolve", "close_unresolved", "release", "assign", "change_priority", "flag"]
_LIVE_END = ["hand_back", "close_chat"]

TABLE: tuple[tuple[str, str, StaffRole | None, str, str, list[str], list[str], list[str]], ...] = (
    (
        "T01",
        "live_queued",
        None,
        "queued",
        "simulated_on_shift",
        ["claim", "claim_and_join", "flag"],
        ["claim", "assign", "change_priority", "flag"],
        [],
    ),
    (
        "T02",
        "unassigned",
        None,
        "not_live",
        "nobody_online",
        ["claim", "flag"],
        ["claim", "assign", "change_priority", "flag"],
        [],
    ),
    ("T03", "claimed", REP, "not_live", "nobody_online", list(_REP_WORK), list(_SUP_ASSIGN), []),
    ("T04", "claimed", REP, "queued", "simulated_on_shift", ["join_chat", *_REP_WORK], list(_SUP_ASSIGN), []),
    (
        "T05",
        "claimed",
        REP,
        "joined",
        "simulated_on_shift",
        ["send_live_message", *_LIVE_END, *_REP_WORK],
        list(_SUP_ASSIGN),
        [],
    ),
    ("T06", "claimed", REP, "handed_back", "simulated_on_shift", list(_REP_WORK), list(_SUP_ASSIGN), []),
    ("T07", "claimed", REP, "closed", "simulated_on_shift", list(_REP_WORK), list(_SUP_ASSIGN), []),
    ("T08", "in_progress", REP, "not_live", "nobody_online", _REP_WORK[1:], list(_SUP_ASSIGN), []),
    (
        "T09",
        "in_progress",
        REP,
        "joined",
        "simulated_on_shift",
        ["send_live_message", *_LIVE_END, *_REP_WORK[1:]],
        list(_SUP_ASSIGN),
        [],
    ),
    ("T10", "waiting", REP, "not_live", "nobody_online", ["start", "release", "flag"], list(_SUP_ASSIGN), []),
    ("T11", "claimed", SUP, "not_live", "nobody_online", ["flag"], ["start", *_SUP_OWN], []),
    ("T12", "in_progress", SUP, "not_live", "nobody_online", ["flag"], list(_SUP_OWN), []),
    (
        "T13",
        "waiting",
        SUP,
        "not_live",
        "nobody_online",
        ["flag"],
        ["start", "release", "assign", "change_priority", "flag"],
        [],
    ),
    ("T14", "resolved", REP, "not_live", "nobody_online", ["flag"], ["flag"], []),
    ("T15", "closed_unresolved", SUP, "not_live", "nobody_online", ["flag"], ["flag"], []),
    (
        "T16",
        "unassigned",
        None,
        "not_live",
        "simulated_on_shift",
        ["claim", "flag"],
        ["claim", "assign", "change_priority", "flag"],
        [],
    ),
)

REPRESENTATIVE_EXAMPLES: dict[str, tuple[str, StaffRole | None, str, str, list[str]]] = {
    "getCase.DEFAULT": ("unassigned", None, "not_live", "nobody_online", ["claim", "flag"]),
    "getCase.WAITING": ("waiting", REP, "not_live", "nobody_online", ["start", "release", "flag"]),
    "getCase.LIVE_JOINED": (
        "in_progress",
        REP,
        "joined",
        "simulated_on_shift",
        [
            "send_live_message",
            "hand_back",
            "close_chat",
            "log_call",
            "log_email",
            "wait",
            "resolve",
            "close_unresolved",
            "release",
            "flag",
        ],
    ),
    "applyCaseAction.CLAIMED": (
        "claimed",
        REP,
        "not_live",
        "nobody_online",
        ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"],
    ),
}
