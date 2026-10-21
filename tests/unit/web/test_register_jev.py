"""AEA-18 S-6: register_jev provides the one shared httpx client and a model -> JevAdapter factory.

Labels: [invariant] wiring facts that must always hold; [negative] the key never shows and no request is made.
"""

from __future__ import annotations

import types
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.policy.limits import Limits
from meridian.web.container import Container, Key, register_jev

KEY = "test-openrouter-key-not-real-0001"
HTTP_KEY = Key[httpx.Client]("jev_http_client")
FACTORY_KEY = Key[Callable[[str], JevAdapter]]("jev_adapter_factory")


def _container() -> Container:
    settings = types.SimpleNamespace(openrouter_api_key=SecretStr(KEY))
    container = Container(settings=settings, limits=Limits())
    assert register_jev(container, FastAPI(), settings=container.settings, limits=container.limits) is None
    return container


def test_register_jev_provides_client_and_factory() -> None:
    """[invariant] one shared client (no redirects, closed on shutdown) and a factory that binds the key; [negative] no key in reprs."""
    c = _container()
    c.build()
    client = c.get(HTTP_KEY)
    assert isinstance(client, httpx.Client)
    assert client.follow_redirects is False
    assert client.timeout == httpx.Timeout(5.0)

    make = c.get(FACTORY_KEY)
    adapter = make("typesafe/jev-1.13")
    assert isinstance(adapter, JevAdapter)
    assert adapter.model == "typesafe/jev-1.13"
    with pytest.raises(ValueError):
        make("typesafe/unknown")
    for text in (repr(make), repr(adapter), str(vars(adapter))):
        assert KEY not in text

    assert c.get(HTTP_KEY) is client
    c.close()
    assert client.is_closed is True

    doc = register_jev.__doc__ or ""
    assert "AEA-18" in doc
    assert "No-op until" not in doc


def test_register_jev_makes_no_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """[negative] registering, building, making an adapter and closing never sends a request."""
    sent: list[object] = []

    def refuse(self: httpx.Client, *args: Any, **kwargs: Any) -> httpx.Response:
        sent.append(args)
        raise AssertionError("register_jev must not make a request")

    monkeypatch.setattr(httpx.Client, "send", refuse)
    c = _container()
    c.build()
    c.get(FACTORY_KEY)("typesafe/jev-1.13")
    c.close()
    assert sent == []
