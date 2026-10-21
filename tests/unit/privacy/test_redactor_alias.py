"""AEA-04 AC-10: `redact` satisfies `Redactor` (read by the type checker) and the alias has the documented shape."""

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meridian.privacy.redact import RedactionProfile, Redactor, redact

    _AS_REDACTOR: Redactor = redact

    def _one_arg(text: str) -> str:
        return text

    _WRONG_SHAPE: Redactor = _one_arg  # type: ignore[assignment]

    def _bind_store(fn: Redactor) -> Callable[[str], str]:
        return lambda t: fn(t, RedactionProfile.STORE).text


def test_redact_satisfies_redactor_alias() -> None:
    rd = importlib.import_module("meridian.privacy.redact")
    assert rd.Redactor == Callable[[str, rd.RedactionProfile], rd.Redacted]
    assert isinstance(rd.redact("x", rd.RedactionProfile.STORE), rd.Redacted)
