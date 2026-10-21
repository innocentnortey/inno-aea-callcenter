"""Ingestion manifest: every issued KB file, its status and why (PRD R-9, R-10; DEC-4)."""
from __future__ import annotations

MANIFEST: dict[str, dict] = {
    "faq/customer_faq.md": {"status": "current", "version": "Last updated 2026-03-02", "topics": "billing,booking,hours,area,payment"},
    "faq/faq_old_copy.md": {"status": "excluded", "why": "Undated old copy contradicting the dated FAQ ($79 diagnostic, $129 after-hours, old hours) — DEC-4, audit K-1/K-2/K-4"},
    "faq/troubleshooting_before_you_call.md": {"status": "current", "version": "undated", "topics": "self-checks"},
    "policies/escalation_and_safety.md": {"status": "current", "version": "Rev 2026-01", "topics": "safety,escalation",
                                          "note": "Rules enforced in code; customer-facing only for its safety instruction and what agents can resolve"},
    "policies/service_area.md": {"status": "current", "version": "Updated 2026-04-01", "topics": "area"},
    "policies/holiday_hours_2026.png": {"status": "current", "version": "2026 (image)", "topics": "hours",
                                        "transcription": "data/kb_transcriptions/holiday_hours_2026.md"},
    "pricing/2026_fee_schedule.pdf": {"status": "current", "version": "Effective 2026-01-01, supersedes all prior", "topics": "billing,membership"},
    "pricing/repair_price_book_2026.csv": {"status": "current", "version": "2026", "topics": "prices"},
    "services/service_catalog.md": {"status": "current", "version": "Last updated 2026-02-10", "topics": "services,prices"},
    "services/scheduling_guide.md": {"status": "excluded", "why": "Rev 2024-11: 48-hour rule contradicts the current 24-hour rule; overflow/waitlist not in the DB — DEC-4 (round 3), audit K-5"},
    "services/technician_arrival_and_etas.md": {"status": "current", "version": "undated", "topics": "booking,late"},
    "services/duct_cleaning.md": {"status": "stub", "why": "TODO stub; the catalog's 'not offered, referral on request' is the answer (audit K-14)"},
    "membership/comfort_club_overview.md": {"status": "current", "version": "Effective 2026-01-01", "topics": "membership"},
    "archive/comfort_club_overview.md": {"status": "excluded", "why": "Superseded membership terms ($149, refund any time, transfers) — DEC-4, audit K-6/K-7"},
    "archive/warranty_terms_2023.txt": {"status": "excluded", "why": "Superseded 2023 warranty (90-day repair, 1-year install) — DEC-4, audit K-8/K-9"},
    "warranty/warranty_policy.md": {"status": "current", "version": "Effective 2025-06-15", "topics": "warranty"},
    "internal/agent_discretion_notes.md": {"status": "staff_only", "why": "'Do not read this document to customers' — audit K-15; staff views only"},
}
