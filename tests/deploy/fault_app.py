"""Test-only (AEA-50 AC-12): the first process started with AEA50_FAULT_ONCE_FILE present answers /healthz 503.

Mounted read-only into a container at run time and selected by swapping the factory name in the image's own start
command. It is never part of the image, and nothing in the image or railway.json can select it (AC-13).
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from meridian.services.health import Heartbeat

# isort: split
from scripts.serve import create_deployed_app


def _never_fresh(self: Heartbeat, mono: float) -> bool:
    return False


def create_faulty_app() -> FastAPI:
    once = Path(os.environ["AEA50_FAULT_ONCE_FILE"])
    if once.exists():
        once.unlink()
        Heartbeat.fresh = _never_fresh  # type: ignore[method-assign]
    return create_deployed_app()
