"""Staff login sessions, the role switch and the flag service (AEA-44, stage7/staff.md section 2).

Decisions: STF-3 (role lives on the session), STF-4 (absolute lifetime), STF-5 (HMAC-keyed token hash), STF-20 (the
refusal reason is always sent), STF-22 (``signed_in_at`` is the demo reading at login). No logging here: the token,
username and password never reach a log, record or span.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from types import MappingProxyType
from typing import Literal

from pydantic import Field, SecretStr, field_validator

from meridian.adapters.sqlite.repos_staff import FlagRow, StaffSessionRow
from meridian.domain.common import CaseRef, MeridianModel
from meridian.domain.staff import (
    STAFF_PERSONAS,
    DemoRole,
    IssuedSession,
    LoginSession,
    LoginSessionId,
    RoleRefusal,
    SessionExpired,
    SessionInfoData,
    SessionMissing,
    StaffActor,
    StaffRole,
)
from meridian.domain.staff import actor_for as persona_actor
from meridian.ports.runtime import Clock, UnitOfWorkFactory

FLAG_TEXT_MAX = 2000
_FLAG_ID = re.compile(r"^flg-([1-9][0-9]{0,17})$")
_TOO_LONG = "at most 2000 characters"
_NOT_IN_CASE = "not a message of this case"


class RoleCard(MeridianModel):
    role: DemoRole
    display_name: str
    sees: tuple[str, ...]
    sees_line: str


ROLE_CARDS: Mapping[DemoRole, RoleCard] = MappingProxyType(
    {
        DemoRole.CUSTOMER: RoleCard(
            role=DemoRole.CUSTOMER,
            display_name="Customer (demo)",
            sees=("Chat", "Demo guide", "Demo inbox", "Monitoring", "Evaluation"),
            sees_line="The chat, the demo guide, the demo inbox, monitoring and evaluation",
        ),
        DemoRole.REPRESENTATIVE: RoleCard(
            role=DemoRole.REPRESENTATIVE,
            display_name="Riley, demo representative",
            sees=("Queue", "Cases", "Live chat", "Review list"),
            sees_line="The queue and cases; can claim, join, reply, log, flag",
        ),
        DemoRole.SUPERVISOR: RoleCard(
            role=DemoRole.SUPERVISOR,
            display_name="Demo supervisor",
            sees=("Oversight", "Review list", "Queue", "Demo controls"),
            sees_line="Urgent, unowned, due-soon, overdue and stuck cases; assigns; runs the demo shift and clock",
        ),
        DemoRole.OWNER: RoleCard(
            role=DemoRole.OWNER,
            display_name="Demo business owner",
            sees=("Outcomes", "Cases (read only)"),
            sees_line="Outcomes, and opens the cases behind them (read only)",
        ),
    }
)


class SessionGone(LookupError):
    """The login session row no longer exists (logged out or expired after the gate resolved it)."""


class StaffSessionStore:
    """Implements web.deps.LoginSessions and StaffAccess, plus ``switch_role``."""

    def __init__(
        self, uow: UnitOfWorkFactory, session_secret: SecretStr, demo_clock: Clock, lifetime_s: int
    ) -> None:
        if lifetime_s <= 0:
            raise ValueError("lifetime_s must be positive")
        self._uow = uow
        self._secret = session_secret
        self._demo_clock = demo_clock
        self._lifetime_s = lifetime_s

    @property
    def lifetime_s(self) -> int:
        return self._lifetime_s

    def _hash(self, token: str) -> str:
        key = self._secret.get_secret_value().encode("utf-8")
        return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _session_of(row: StaffSessionRow) -> LoginSession:
        return LoginSession(
            session_id=row.session_id,
            role=row.role,
            role_reset=row.role_reset_pending,
            signed_in_at=row.signed_in_demo,
            expires_at=row.expires_real,
        )

    def start(self, now: datetime) -> IssuedSession:
        wall = now.astimezone(UTC)
        token = secrets.token_urlsafe(32)
        session_id = LoginSessionId(str(uuid.uuid4()))
        demo = self._demo_clock.now().astimezone(UTC)  # exactly one demo-clock reading (STF-22)
        row = StaffSessionRow(
            token_hash=self._hash(token),
            session_id=session_id,
            role=DemoRole.CUSTOMER,
            role_reset_pending=False,
            signed_in_demo=demo,
            created_real=wall,
            expires_real=wall + timedelta(seconds=self._lifetime_s),
        )
        with self._uow(write=True) as tx:
            tx.staff.sessions.insert(row)
            tx.commit()
        return IssuedSession(session=self._session_of(row), token=SecretStr(token))

    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired:
        raw = token.get_secret_value()
        if not raw:
            return SessionMissing()
        token_hash = self._hash(raw)
        with self._uow() as tx:
            row = tx.staff.sessions.by_token_hash(token_hash)
        if row is None:
            return SessionMissing()
        if row.expires_real <= now:
            with self._uow(write=True) as tx:
                tx.staff.sessions.delete(token_hash)
                tx.commit()
            return SessionExpired()
        return self._session_of(row)  # read only: the lifetime is absolute

    def end(self, token: SecretStr) -> None:
        raw = token.get_secret_value()
        if not raw:
            return
        token_hash = self._hash(raw)
        with self._uow(write=True) as tx:
            tx.staff.sessions.delete(token_hash)
            tx.commit()

    def session_info(self, session: LoginSession) -> SessionInfoData:
        card = ROLE_CARDS[session.role]
        return SessionInfoData(
            role=session.role,
            display_name=card.display_name,
            sees=card.sees,
            signed_in_at=session.signed_in_at,
        )

    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal:
        """Pure: no unit of work, no clock. Never clears ``role_reset`` (only ``switch_role`` does)."""
        if session.role.value in {r.value for r in needs}:
            return persona_actor(StaffRole(session.role.value))
        return RoleRefusal(
            role=session.role,
            needs=tuple(needs),
            reason="role_reset" if session.role_reset else "wrong_role",
        )

    def switch_role(self, session_id: LoginSessionId, role: DemoRole) -> LoginSession:
        with self._uow(write=True) as tx:
            if not tx.staff.sessions.set_role(session_id, role):
                raise SessionGone("login session not found")
            row = tx.staff.sessions.by_session_id(session_id)
            tx.commit()
        if row is None:
            raise SessionGone("login session not found")
        return self._session_of(row)


class FlagIn(MeridianModel):
    case_ref: CaseRef
    target: Literal["answer", "brief", "escalation"]
    message_id: str | None
    note: str | None = Field(default=None, max_length=FLAG_TEXT_MAX)
    reason: str | None = Field(default=None, max_length=FLAG_TEXT_MAX)

    @field_validator("note", "reason", mode="after")
    @classmethod
    def _blank_is_none(cls, v: str | None) -> str | None:
        return None if v is not None and v == "" else v


class FlagRecord(MeridianModel):
    flag_id: str
    target: str
    reason: str | None
    case_ref: CaseRef
    message_id: str | None
    note: str | None
    flagged_by: str
    at: datetime
    status: Literal["new", "reviewed"]
    reviewed_by: str | None
    reviewed_note: str | None


class FlagRejected(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "FLAG_NOT_FOUND", "VALIDATION_ERROR"]
    field: str | None
    constraint: str | None
    details: dict[str, str] | None


def _clean(v: str | None) -> str | None:
    if v is None:
        return None
    stripped = v.strip()
    return stripped or None


def _reject(
    code: Literal["CASE_NOT_FOUND", "FLAG_NOT_FOUND", "VALIDATION_ERROR"],
    *,
    field: str | None = None,
    constraint: str | None = None,
    details: dict[str, str] | None = None,
) -> FlagRejected:
    return FlagRejected(code=code, field=field, constraint=constraint, details=details)


def _record(row: FlagRow) -> FlagRecord:
    return FlagRecord(
        flag_id=f"flg-{row.id}",
        target=row.target,
        reason=row.reason,
        case_ref=row.case_ref,
        message_id=row.message_id,
        note=row.note,
        flagged_by=STAFF_PERSONAS[row.flagged_by_role].signature,
        at=row.flagged_at,
        status=row.status,
        reviewed_by=None if row.reviewed_by_role is None else STAFF_PERSONAS[row.reviewed_by_role].signature,
        reviewed_note=row.reviewed_note,
    )


class FlagService:
    """Flags for the review list. Writes only ``flags`` (R-37); reads ``cases`` and ``messages`` for checks."""

    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock) -> None:
        self._uow = uow
        self._demo_clock = demo_clock

    def flag(self, flag: FlagIn, actor: StaffActor) -> FlagRecord | FlagRejected:
        note, reason = _clean(flag.note), _clean(flag.reason)
        for name, value in (("note", note), ("reason", reason)):
            if value is not None and len(value) > FLAG_TEXT_MAX:
                return _reject("VALIDATION_ERROR", field=name, constraint=_TOO_LONG)
        at = self._demo_clock.now().astimezone(UTC)
        with self._uow(write=True) as tx:
            if tx.core.cases_ro.owner(flag.case_ref) is None:
                return _reject("CASE_NOT_FOUND", details={"reference": str(flag.case_ref)})
            if flag.message_id is not None and not tx.core.messages.belongs_to_case(
                flag.message_id, flag.case_ref
            ):
                return _reject("VALIDATION_ERROR", field="message_id", constraint=_NOT_IN_CASE)
            row = FlagRow(
                case_ref=flag.case_ref,
                target=flag.target,
                message_id=flag.message_id,
                note=note,
                reason=reason,
                flagged_by_role=actor.role,
                flagged_at=at,
                status="new",
                reviewed_by_role=None,
                reviewed_note=None,
                reviewed_at=None,
            )
            new_id = tx.staff.flags.insert(row)
            tx.commit()
        return _record(row.model_copy(update={"id": new_id}))

    def review(self, flag_id: str, note: str | None, actor: StaffActor) -> FlagRecord | FlagRejected:
        m = _FLAG_ID.fullmatch(flag_id)
        if m is None:
            return _reject("FLAG_NOT_FOUND")
        note_c = _clean(note)
        if note_c is not None and len(note_c) > FLAG_TEXT_MAX:
            return _reject("VALIDATION_ERROR", field="note", constraint=_TOO_LONG)
        at = self._demo_clock.now().astimezone(UTC)
        numeric = int(m.group(1))
        with self._uow(write=True) as tx:
            if not tx.staff.flags.review(numeric, actor.role, note_c, at):
                return _reject("FLAG_NOT_FOUND", details={"flag_id": flag_id})
            row = tx.staff.flags.get(numeric)
            tx.commit()
        if row is None:
            raise LookupError("flag vanished inside its own transaction")
        return _record(row)

    def list_flags(self) -> tuple[FlagRecord, ...]:
        with self._uow() as tx:
            rows = tx.staff.flags.list_ordered()
        return tuple(_record(r) for r in rows)
