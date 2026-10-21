"""Fixtures for tests/unit/domain only (AEA-02). Sentinels are built at run time so no real secret, code or phone is ever
written in the repository."""

from __future__ import annotations

import secrets
from collections.abc import Callable

import pytest


@pytest.fixture
def make_sentinel() -> Callable[[str], str]:
    """Return a function that builds a distinctive, never-real value: a prefix plus random hex."""

    def build(prefix: str) -> str:
        return f"{prefix}-{secrets.token_hex(8)}"

    return build


@pytest.fixture
def make_digits() -> Callable[[], str]:
    """Return a function that builds a six-digit string (a stand-in verification code) at run time."""

    def build() -> str:
        return "".join(secrets.choice("0123456789") for _ in range(6))

    return build


@pytest.fixture
def make_phone() -> Callable[[], str]:
    """Return a function that builds a fake phone number at run time (never a real one)."""

    def build() -> str:
        return "+1555" + "".join(secrets.choice("0123456789") for _ in range(7))

    return build
