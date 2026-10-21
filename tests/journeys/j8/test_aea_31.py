"""J-8 (proposed extension, slice plan section 0a): a demo reset from one client.

Level today: mock-tested (real ResetService, real AEA-23 owned_thread and require_staff on a minimal FastAPI app over a
temp SQLite copy; no server, no login, a StaffAccess double that reads the stored role_reset_pending flag). Integrated
level blocked by AEA-57 (harness) and AEA-52 (J-8).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.domain.common import ThreadId
from meridian.domain.staff import DemoRole, LoginSession, LoginSessionId, RoleRefusal, StaffRole, actor_for
from meridian.services.reset import ResetDone
from meridian.web.deps import (
    get_login_session,
    get_staff_access,
    get_uow_factory,
    owned_thread,
    require_staff,
)
from meridian.web.errors import ApiProblem, handle_api_problem
from tests.services.reset_support import (
    WALL,
    count,
    demo_store,
    issued_rows,
    make_dirty_demo,
    make_service,
    new_request_id,
    rows,
)

pytestmark = pytest.mark.journey

HEADER = "X-Test-Session"


class _StaffAccessDouble:
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> Any:
        if session.role_reset:
            return RoleRefusal(role=session.role, needs=needs, reason="role_reset")
        if session.role.value not in {n.value for n in needs}:
            return RoleRefusal(role=session.role, needs=needs, reason="wrong_role")
        return actor_for(StaffRole(session.role.value))


def test_j8_reset_ends_chat_resets_roles_restores_tables() -> None:
    with demo_store() as (store, cp):
        dirty = make_dirty_demo(store, cp)
        svc, _ = make_service(store, cp)
        rep, sup, cust = (dirty.sessions[k] for k in ("representative", "supervisor", "customer"))
        app = FastAPI()
        app.add_exception_handler(ApiProblem, handle_api_problem)

        @app.get("/t/{thread_id}")
        def thread_route(thread_id: ThreadId = Depends(owned_thread)) -> dict[str, str]:  # noqa: B008
            return {"ok": "yes"}

        @app.get("/staff")
        def staff_route(
            actor: Any = Depends(require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR)),  # noqa: B008
        ) -> dict[str, str]:
            return {"ok": "yes"}

        def session_from_header(request: Request) -> LoginSession:
            sid = request.headers[HEADER]
            role, pending = rows(
                store.db_path,
                "SELECT role, role_reset_pending FROM staff_sessions WHERE session_id = ?",
                (sid,),
            )[0]
            return LoginSession(
                session_id=LoginSessionId(sid),
                role=DemoRole(role),
                role_reset=bool(pending),
                signed_in_at=DEMO_START,
                expires_at=WALL + timedelta(hours=12),
            )

        def uow_factory() -> Any:
            return store.uow

        def staff_access() -> _StaffAccessDouble:
            return _StaffAccessDouble()

        app.dependency_overrides[get_uow_factory] = uow_factory
        app.dependency_overrides[get_login_session] = session_from_header
        app.dependency_overrides[get_staff_access] = staff_access
        http = TestClient(app)
        tab_a = {HEADER: str(rep.session_id)}  # two tabs on login L1
        tab_b = {HEADER: str(rep.session_id)}
        client_c = {HEADER: str(sup.session_id)}  # login L2

        for headers in (tab_a, tab_b, client_c):
            assert http.get("/staff", headers=headers).status_code == 200

        done = svc.reset(
            WALL, request_id=new_request_id(), session_id=rep.session_id, role=DemoRole.REPRESENTATIVE
        )
        assert isinstance(done, ResetDone)
        assert done.roles_reset == 2
        assert done.open_chats_ended == 1

        for headers in (tab_a, tab_b, client_c):
            refused = http.get("/staff", headers=headers)
            assert refused.status_code == 403
            body = refused.json()["error"]
            assert body["code"] == "ROLE_NOT_ALLOWED"
            assert body["details"]["reason"] == "role_reset"

        gone = http.get(f"/t/{dirty.open_threads[0]}", headers={HEADER: str(cust.session_id)})
        assert gone.status_code == 410
        assert gone.json()["error"]["code"] == "SESSION_ENDED"
        assert count(store.db_path, "events") >= 1
        assert (
            rows(
                store.db_path,
                "SELECT COUNT(*) FROM events WHERE stream = ? AND type = 'demo_reset'",
                (str(dirty.open_threads[0]),),
            )[0][0]
            == 1
        )
        for table in ("customers", "technicians", "appointment_slots", "appointments", "invoices"):
            assert rows(store.db_path, f"SELECT * FROM {table} ORDER BY rowid") == issued_rows(  # noqa: S608
                store.issued_path, table
            )

        # CON-10 switchRole is AEA-44's; this raw UPDATE stands in for it at mock level.
        with store.uow(write=True) as tx:
            tx.connection.execute(
                "UPDATE staff_sessions SET role='representative', role_reset_pending=0 WHERE session_id=?",
                (str(rep.session_id),),
            )
            tx.commit()
        for headers in (tab_a, tab_b):
            assert (
                http.get("/staff", headers=headers).status_code == 200
            )  # the role is per login, shared by tabs
        still = http.get("/staff", headers=client_c)
        assert still.status_code == 403
        assert still.json()["error"]["details"]["reason"] == "role_reset"
