"""J-10 read leg (AEA-48). **Level today: mock-tested** - the real AEA-23 app and middleware in process with AEA-48's
router, the real login route over a session-store double, and a MetricsReads double whose mappings stand in for the
stored aggregates; no server, no browser, no DB copy. Blocked steps: the same three reads over MetricsReader on stored
rows (AEA-53, which lands J-10) and the integrated run (AEA-57 harness). Stored side at this level: the double's
mappings only."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from meridian.domain.staff import DemoRole
from meridian.web.schemas.reads import MEASURE_UNITS
from tests.api.reads_support import OPERATIONS, FakeMetricsReads, all_measures, get_read, reads_app
from tests.api.web_shell_support import (
    assert_matches,
    cookie_header,
    login,
    make_client,
    make_settings,
    session_cookie_value,
)

pytestmark = pytest.mark.journey


def test_j10_read_pages_show_stored_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    reads = FakeMetricsReads()
    stored = copy.deepcopy(reads.returns)
    settings = make_settings(tmp_path)
    h = reads_app(monkeypatch, settings, reads=reads)
    with make_client(h.app) as client:
        token = session_cookie_value(login(client, settings))
        assert token
        h.store.set_role(token, DemoRole.OWNER)
        responses = {op: get_read(client, op, cookie_header(token)) for op in OPERATIONS}
    for op, r in responses.items():
        assert r.status_code == 200
        assert_matches(r, op)
        assert r.json() == stored[op]  # what the user sees equals what is stored
    measures = all_measures({op: r.json() for op, r in responses.items()})
    units: set[str] = set()
    for m in measures:
        assert isinstance(m["label"], str) and m["label"]
        if "unit" in m:
            assert m["unit"] in MEASURE_UNITS
            units.add(m["unit"])
        if m.get("unit") == "share" and m["value"] is not None:
            assert isinstance(m["denominator"], int) and m["denominator"] > 0
            assert 0 <= m["value"] <= 1
        if "unit" not in m:
            assert m["denominator"] > 0
            assert 0 <= m["value"] <= 1
    print("units seen:", sorted(units), "measures checked:", len(measures))
    assert reads.calls == list(OPERATIONS)  # one stored read per page, nothing recomputed


def test_j10_read_pages_from_metrics_reader_on_db_copy() -> None:
    pytest.skip(
        "blocked: MetricsReader over stored rows on the DB copy (AEA-53, lands J-10); journey harness (AEA-57)"
    )
