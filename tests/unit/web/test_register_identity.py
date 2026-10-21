"""AEA-27 PA-7: the register_identity hunk provides the one IdentityService from the secret and the limits."""

from __future__ import annotations

import secrets
import types
from datetime import timedelta
from typing import Any

from fastapi import FastAPI
from pydantic import SecretStr

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.domain.identity import CodeSent, Located, Locator
from meridian.policy.limits import Limits
from meridian.services.identity import IdentityService
from meridian.web.container import Container, Key, register_identity
from tests.fixtures.sqlite import temp_sqlite
from tests.services.identity_support import customer_contact
from tests.unit.adapters.sqlite.helpers import new_thread


def test_register_identity_builds_one_service() -> None:
    with temp_sqlite() as store:
        settings = types.SimpleNamespace(session_secret=SecretStr(secrets.token_urlsafe(32)))
        limits = Limits()
        c = Container(settings=settings, limits=limits)
        try:
            c.provide(Key[Any]("uow_factory"), lambda _c: store.uow)
            register_identity(c, FastAPI(), settings=c.settings, limits=limits)
            c.build()

            svc = c.get(Key[IdentityService]("identity_service"))
            assert isinstance(svc, IdentityService)
            assert svc is c.get(Key[IdentityService]("identity_service"))

            name, phone = customer_contact(store, "MHC-10002")
            thread = new_thread()
            located = svc.locate(thread, Locator(name=name, phone=SecretStr(phone)), DEMO_START)
            assert isinstance(located, Located)
            sent = svc.send_code(thread, "session-a", DEMO_START)
            assert isinstance(sent, CodeSent)
            assert sent.expires_at == DEMO_START + timedelta(seconds=limits.identity.code_ttl_s)
        finally:
            c.close()
    doc = register_identity.__doc__ or ""
    assert "No-op until" not in doc
    assert "AEA-27" in doc
