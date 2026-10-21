"""The journey client: httpx with cookies, every API response checked against the signed OpenAPI (AEA-57; web.md section 13)."""

from __future__ import annotations

from collections.abc import Mapping

import httpx

from tests.api.openapi_check import assert_response_matches


def check_page_response(response: httpx.Response) -> None:
    if "X-Request-ID" not in response.headers:
        raise AssertionError(f"{response.request.url.path}: response carries no X-Request-ID")


def set_cookie_lines(response: httpx.Response) -> list[str]:
    return response.headers.get_list("set-cookie")


def cookie_attributes(line: str) -> dict[str, str | None]:
    """`mhc_session=abc; Path=/; HttpOnly` -> {"mhc_session": "abc", "path": "/", "httponly": None}."""
    parts = [p.strip() for p in line.split(";") if p.strip()]
    out: dict[str, str | None] = {}
    for index, part in enumerate(parts):
        name, sep, value = part.partition("=")
        key = name if index == 0 else name.lower()
        out[key] = value if sep else None
    return out


class JourneyClient:
    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None) -> None:
        # 70 s: the turn deadline is 60 s and the browser gives up at 65 s
        self._http = httpx.Client(
            base_url=base_url, follow_redirects=False, timeout=httpx.Timeout(70.0), transport=transport
        )
        self.responses: list[httpx.Response] = []

    def call(
        self,
        method: str,
        path: str,
        *,
        operation_id: str | None,
        body: object | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        if path.startswith("/api/") and operation_id is None:
            raise AssertionError(f"{method} {path}: an API step must name its operationId")
        response = self._http.request(method, path, json=body, headers=headers)
        self.responses.append(response)
        if operation_id is not None:
            try:
                assert_response_matches(response, operation_id)
            except AssertionError as exc:
                raise AssertionError(f"{operation_id} -> HTTP {response.status_code}: {exc}") from None
        else:
            check_page_response(response)
        return response

    def cookie(self, name: str = "mhc_session") -> str | None:
        return self._http.cookies.get(name)

    def close(self) -> None:
        self._http.close()
