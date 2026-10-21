"""AEA-24 AC-11: the inbox code, demo password, eval key and held-out expected output never reach an output."""

from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path
from typing import Any

from eval.harness.tests.fixture_cases import (
    ISSUED_DB,
    item,
    run_secrets,
    simple_case,
    simple_key,
    wp4_case,
    wp4_key,
    wp4_scripted,
    write_cases,
    write_sealed_heldout,
)
from eval.harness.tests.stub_app import StubCall, text_block
from eval.harness.tests.support import Outcome, assert_absent, base_argv, make_stub, run_cli


def _seed_values() -> list[str]:
    con = sqlite3.connect(f"file:{ISSUED_DB}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT name, phone, email, service_address FROM customers WHERE customer_id = 'MHC-57204'"
        ).fetchone()
    finally:
        con.close()
    return [v for v in row if v]


def test_code_password_eval_key_absent_from_outputs(tmp_path: Path) -> None:
    """negative: across a dev run, a load run and a held-out run, no known secret is in the log, the results, the
    JSON, the Markdown or the timings file, even when the agent's reply echoes one."""
    run = run_secrets()
    seeds = _seed_values()
    outcomes: list[tuple[str, Outcome]] = []
    secret_values = [run.eval_key, run.password, run.username]

    def leaky(call: StubCall) -> str:
        return f"ref {call.state.last_code} {run.password}"

    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    dev_stub = make_stub(run, wp4_scripted(charged=True, extra=leaky))
    dev_cases = write_cases(dev_dir / "cases", [(wp4_case(), wp4_key())])
    dev = run_cli(dev_dir, base_argv(dev_cases, dev_dir / "reports", repeats=2), stub=dev_stub, run=run)
    outcomes.append(("dev run", dev))
    assert dev.report()["results"], "the dev run scored its case"

    load_dir = tmp_path / "load"
    load_dir.mkdir()
    load_stub = make_stub(run, wp4_scripted())
    load_cases = write_cases(load_dir / "cases", [(wp4_case(), wp4_key())])
    load_argv = base_argv(load_cases, load_dir / "reports", suite="load", extra=["--conversations", "2"])
    load = run_cli(load_dir, load_argv, stub=load_stub, run=run)
    outcomes.append(("load run", load))
    assert load.timings(), "the load run wrote its timings file"

    held_dir = tmp_path / "held"
    held_dir.mkdir()
    expected = "held-out-expect-" + secrets.token_hex(4)
    forbidden = "held-out-forbid-" + secrets.token_hex(4)
    key = simple_key("H-1", must_say=[item(expected)], must_not_say=[item(forbidden)])
    write_sealed_heldout(held_dir / "cases", held_dir / "keys", [(simple_case("H-1", split="held-out"), key)])
    held_stub = make_stub(run, lambda call: call.reply([text_block(f"The reply mentions {forbidden}.")]))
    held_argv = base_argv(
        held_dir / "cases",
        held_dir / "reports",
        split="held-out",
        extra=["--heldout-key-dir", str(held_dir / "keys")],
    )
    held = run_cli(held_dir, held_argv, stub=held_stub, run=run)
    outcomes.append(("held-out run", held))

    issued = dev_stub.issued_codes + load_stub.issued_codes
    assert len(issued) >= 3
    for name, outcome in outcomes:
        assert outcome.code != 5, f"{name}: a leak was blocked, so the output was not written"
        text = outcome.all_text()
        assert_absent(text, [*secret_values, *issued], where=name)
        if name != "held-out run":
            assert_absent(text, seeds, where=name)
    assert_absent(held.all_text(), [expected, forbidden], where="held-out run")
    results: list[dict[str, Any]] = dev.report()["results"] + held.report()["results"]
    assert_absent(str(results), [*secret_values, *issued, *seeds, expected, forbidden], where="results")
