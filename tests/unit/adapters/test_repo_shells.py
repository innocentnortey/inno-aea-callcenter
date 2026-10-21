"""AEA-02 AC-17: seven repository shells, one constructor each."""

from __future__ import annotations

import importlib
import sqlite3
import types
from typing import get_type_hints

import pytest

SHELLS = [
    ("meridian.adapters.sqlite.repos_core", "CoreRepos"),
    ("meridian.adapters.sqlite.repos_spend", "SpendRepo"),
    ("meridian.adapters.sqlite.repos_identity", "IdentityRepos"),
    ("meridian.adapters.sqlite.repos_booking", "BookingRepos"),
    ("meridian.adapters.sqlite.repos_cases", "CaseRepos"),
    ("meridian.adapters.sqlite.repos_staff", "StaffRepos"),
    ("meridian.adapters.sqlite.repos_ops", "OpsRepos"),
]


def test_seven_shells_one_constructor() -> None:
    print([name for _, name in SHELLS])
    assert len(SHELLS) == 7
    for module_name, class_name in SHELLS:
        cls = getattr(importlib.import_module(module_name), class_name)
        assert "__init__" in vars(cls)
        assert get_type_hints(cls.__init__) == {"conn": sqlite3.Connection, "return": types.NoneType}
        assert [n for n in vars(cls) if not n.startswith("_")] == [], class_name
        with sqlite3.connect(":memory:") as conn:
            assert cls(conn) is not None


@pytest.mark.parametrize(("module_name", "class_name"), SHELLS)
def test_shell_lives_in_its_own_module(module_name: str, class_name: str) -> None:
    cls = getattr(importlib.import_module(module_name), class_name)
    assert cls.__module__ == module_name
