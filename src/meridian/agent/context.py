"""Constructor dependencies of the graph (GraphDeps) and the one-method ModelsStatus port (graph-core section 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from meridian.policy.limits import Limits
from meridian.ports.runtime import RetrievalIndex, TraceSink, UnitOfWorkFactory

if TYPE_CHECKING:
    from meridian.agent.gateway import ModelGateway  # AEA-20 is on main

__all__ = ["GraphDeps", "ModelsStatus"]

# PD-7: these services are built by later tickets. Until the named module is on main, the field is typed through an
# alias to Any; AEA-51 (or the follow-up of R-3) replaces each alias with the real import.
IdentityService: TypeAlias = Any  # meridian.services.identity.IdentityService (AEA-27)
SchedulingService: TypeAlias = Any  # meridian.services.scheduling.SchedulingService (AEA-28)
HandoffService: TypeAlias = Any  # meridian.services.handoff.HandoffService (AEA-29)
BriefAssembler: TypeAlias = Any  # meridian.services.handoff.BriefAssembler (AEA-29)
DemoService: TypeAlias = Any  # meridian.services.demo.DemoService (AEA-30)
SpecialistRunner: TypeAlias = Any  # meridian.agent.specialists.runner.SpecialistRunner (AEA-35)
CaseService: TypeAlias = Any  # meridian.services.cases.CaseService (AEA-29)


class ModelsStatus(Protocol):
    """LedgerService.models_disabled (models.md section 6): our cap reached or any provider circuit open (R-G-13)."""

    def models_disabled(self) -> bool: ...


@dataclass(frozen=True)
class GraphDeps:  # field names and order exactly graph-core section 4
    gateway: ModelGateway
    retrieval: RetrievalIndex
    uow: UnitOfWorkFactory
    identity: IdentityService
    scheduling: SchedulingService
    handoff: HandoffService
    brief: BriefAssembler
    demo: DemoService
    limits: Limits
    trace: TraceSink
    specialists: SpecialistRunner
    cases: CaseService
    ledger: ModelsStatus
