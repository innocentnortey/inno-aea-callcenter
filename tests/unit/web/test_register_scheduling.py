"""AEA-28 PA-1: the register_scheduling hunk provides the one SchedulingService from the uow factory and limits."""

from __future__ import annotations

import types
from typing import Any

from fastapi import FastAPI

from meridian.domain.common import CustomerId
from meridian.policy.limits import Limits
from meridian.services.scheduling import SchedulingService
from meridian.web.container import Container, Key, register_scheduling
from tests.fixtures.sqlite import temp_sqlite


def test_register_scheduling_provides_one_service() -> None:
    with temp_sqlite() as store:
        c = Container(settings=types.SimpleNamespace(name="stand-in"), limits=Limits())
        try:
            c.provide(Key[Any]("uow_factory"), lambda _c: store.uow)
            register_scheduling(c, FastAPI(), settings=c.settings, limits=c.limits)
            c.build()
            svc = c.get(Key[SchedulingService]("scheduling"))
            assert svc is c.get(Key[SchedulingService]("scheduling"))
            assert isinstance(svc, SchedulingService)
            assert svc._booking is c.limits.booking
            assert svc.slice_inputs(CustomerId("MHC-57204")).zone == "central"
            doc = register_scheduling.__doc__ or ""
            assert "AEA-28" in doc and "No-op until" not in doc
        finally:
            c.close()
