"""MetricsRepo (AEA-53): read-only facts behind the three reads. Rows are written through the real writers."""

from __future__ import annotations

import pytest

from meridian.adapters.sqlite.repos_metrics import MetricsRepo
from meridian.domain.common import HandoffReason
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.services.test_metrics_reader_rows import (
    DEMO_NOW,
    add_case,
    add_conversation,
    add_flag,
    add_turn,
)


def test_conversation_facts_filter_tags_topics_flags() -> None:
    with temp_sqlite() as store:
        live = add_conversation(store.uow, outcome="ai_resolved")
        add_turn(store.uow, live, topic="billing")
        add_turn(store.uow, live, topic="booking")
        add_turn(store.uow, live, topic="billing")
        add_turn(store.uow, live, topic=None)
        ref = add_case(store.uow, live, reason=HandoffReason.REFUND)
        add_flag(store.uow, ref)
        add_flag(store.uow, ref)
        for tag in ("eval", "load", "seed"):
            add_conversation(store.uow, run_tag=tag, outcome="ai_resolved")
        with store.uow() as tx:
            only_live = tx.ops.metrics.conversations(("live",))
            both = tx.ops.metrics.conversations(("live", "seed"))
            with pytest.raises(ValueError, match="run_tags"):
                tx.ops.metrics.conversations(())
            with pytest.raises(ValueError, match="run_tags"):
                tx.ops.metrics.conversations(("bogus",))  # type: ignore[arg-type]
        assert [c.thread_id for c in only_live] == [str(live)]
        assert only_live[0].topics == ("billing", "booking")
        assert only_live[0].flag_count == 2
        assert sorted(c.run_tag for c in both) == ["live", "seed"]


def test_live_turns_need_live_turn_and_conversation() -> None:
    with temp_sqlite() as store:
        live = add_conversation(store.uow)
        add_turn(store.uow, live, server_ms=100)
        eval_conv = add_conversation(store.uow, run_tag="eval")
        add_turn(store.uow, eval_conv, run_tag="live", server_ms=200)  # a live turn on an eval conversation
        add_turn(store.uow, eval_conv, run_tag="eval", server_ms=300)
        with store.uow() as tx:
            turns = tx.ops.metrics.live_turns()
        assert [t.server_ms for t in turns] == [100]


def test_cases_and_promises_join_and_order() -> None:
    with temp_sqlite() as store:
        thread = add_conversation(store.uow, outcome="handed_off")
        safety = add_case(store.uow, thread, reason=HandoffReason.SAFETY, safety_kind="co")
        refund = add_case(store.uow, thread, reason=HandoffReason.REFUND, missed=True)
        other = add_conversation(store.uow, run_tag="eval", outcome="handed_off")
        add_case(store.uow, other, reason=HandoffReason.REFUND)
        with store.uow(write=True) as tx:
            tx.cases.promises.set_status(safety, "changed", DEMO_NOW, "reworded")
            tx.commit()
        with store.uow() as tx:
            cases = tx.ops.metrics.cases(("live",))
            promises = tx.ops.metrics.promises(("live",))
        assert [c.case_ref for c in cases] == [str(safety), str(refund)]  # the eval thread's case is excluded
        assert cases[0].safety_kind == "co"
        assert {p.case_ref for p in promises} == {str(safety), str(refund)}
        dues = [p.due_at for p in promises]
        non_null = [d for d in dues if d is not None]
        assert all(d.utcoffset() is not None for d in non_null)  # aware
        assert non_null == sorted(non_null)  # due ascending
        assert dues == non_null + [None] * (len(dues) - len(non_null))  # nulls last
        assert "changed" in {p.status for p in promises}  # a changed row is returned too


def test_ops_repos_exposes_metrics() -> None:
    with temp_sqlite() as store, store.uow() as tx:
        assert isinstance(tx.ops.metrics, MetricsRepo)
        assert vars(tx.ops.metrics)["_conn"] is tx.connection
