"""The 17-file knowledge-base manifest and the staff-guidance record (AEA-16, stage7/data.md section 3).

Pydantic and standard library only (MC-26): AEA-29 imports `StaffGuidance` without the embedding stack.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Final, Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from meridian.domain.common import MeridianModel, PassageId


class FileStatus(StrEnum):
    CURRENT = "current"
    EXCLUDED = "excluded"
    STAFF_ONLY = "staff_only"
    STUB = "stub"  # PRD R-10


class ParseMethod(StrEnum):
    MARKDOWN = "markdown"
    TEXT = "text"
    PDF_TEXT = "pdf_text"
    CSV_ROWS = "csv_rows"
    PNG_TRANSCRIPTION = "png_transcription"  # data/kb_transcriptions/holiday_hours_2026.md, linked to the PNG


def _check_status_fields(status: FileStatus, version_label: str | None, reason: str | None) -> None:
    if status == FileStatus.CURRENT:
        if not version_label or reason is not None:
            raise PydanticCustomError(
                "manifest_current_row", "a current row needs a version label and no reason"
            )
    elif not reason:
        raise PydanticCustomError("manifest_reason_required", "a non-current row needs a reason")


class ManifestRow(MeridianModel):
    path: str  # relative to knowledge_base/
    status: FileStatus
    version_label: str | None  # as the file states it; None only for non-CURRENT rows
    parse_method: ParseMethod
    reason: str | None  # required when status != CURRENT
    source_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )  # of the issued file's bytes (and the transcription's, for the PNG)
    chunks: int = Field(ge=0)  # 0 for every non-CURRENT row

    @model_validator(mode="after")
    def _check(self) -> ManifestRow:
        _check_status_fields(self.status, self.version_label, self.reason)
        if self.status != FileStatus.CURRENT and self.chunks != 0:
            raise PydanticCustomError("manifest_noncurrent_chunks", "a non-current row has no chunks")
        return self


class ManifestSpec(MeridianModel):
    """The hand-written static part of a row."""

    path: str
    status: FileStatus
    version_label: str | None
    parse_method: ParseMethod
    reason: str | None

    @model_validator(mode="after")
    def _check(self) -> ManifestSpec:
        _check_status_fields(self.status, self.version_label, self.reason)
        return self


class StaffGuidance(MeridianModel):
    """One staff-only bullet (DAT-13); never embedded."""

    passage_id: PassageId  # "internal/agent_discretion_notes.md#<n>"
    file: Literal["internal/agent_discretion_notes.md"]
    section: str
    version_label: str
    text: str
    text_sha256: str

    @model_validator(mode="after")
    def _check(self) -> StaffGuidance:
        if self.text_sha256 != hashlib.sha256(self.text.encode("utf-8")).hexdigest():
            raise PydanticCustomError("staff_guidance_hash_mismatch", "text_sha256 does not match the text")
        return self


def _spec(
    path: str,
    status: FileStatus,
    version_label: str | None,
    parse_method: ParseMethod,
    reason: str | None = None,
) -> ManifestSpec:
    return ManifestSpec(
        path=path, status=status, version_label=version_label, parse_method=parse_method, reason=reason
    )


_C = FileStatus.CURRENT
_X = FileStatus.EXCLUDED
_MD = ParseMethod.MARKDOWN

MANIFEST: Final[tuple[ManifestSpec, ...]] = (
    _spec(
        "archive/comfort_club_overview.md",
        _X,
        None,
        _MD,
        "Superseded membership terms ($149 a year, refunds at any time, transfers to a new address); DEC-4, audit K-6, K-7",
    ),
    _spec(
        "archive/warranty_terms_2023.txt",
        _X,
        "2023",
        ParseMethod.TEXT,
        "Superseded 2023 warranty (90-day repair labour, 1-year installation); DEC-4, audit K-8, K-9",
    ),
    _spec("faq/customer_faq.md", _C, "Last updated 2026-03-02", _MD),
    _spec(
        "faq/faq_old_copy.md",
        _X,
        None,
        _MD,
        "Undated old copy that contradicts the dated FAQ ($79 diagnostic, $129 after-hours, old hours); DEC-4, audit K-1, K-2, K-4",
    ),
    _spec("faq/troubleshooting_before_you_call.md", _C, "undated", _MD),
    _spec(
        "internal/agent_discretion_notes.md",
        FileStatus.STAFF_ONLY,
        "undated",
        _MD,
        'Internal guidance marked "Do not read this document to customers"; staff views only through staff_notes.json, never embedded; audit K-15',
    ),
    _spec("membership/comfort_club_overview.md", _C, "Effective 2026-01-01", _MD),
    _spec("policies/escalation_and_safety.md", _C, "Rev 2026-01", _MD),
    _spec("policies/holiday_hours_2026.png", _C, "2026 (image)", ParseMethod.PNG_TRANSCRIPTION),
    _spec("policies/service_area.md", _C, "Updated 2026-04-01", _MD),
    _spec(
        "pricing/2026_fee_schedule.pdf",
        _C,
        "Effective 2026-01-01, supersedes all prior",
        ParseMethod.PDF_TEXT,
    ),
    _spec("pricing/repair_price_book_2026.csv", _C, "2026", ParseMethod.CSV_ROWS),
    _spec(
        "services/duct_cleaning.md",
        FileStatus.STUB,
        None,
        _MD,
        'TODO stub; the service catalog\'s "Not offered" list answers duct cleaning (referral on request); audit K-14, DAT-18',
    ),
    _spec(
        "services/scheduling_guide.md",
        _X,
        "Rev 2024-11",
        _MD,
        "Rev 2024-11: its 48-hour rule contradicts the current 24-hour rule, and its overflow and waitlist slots are not in the DB; DEC-4, audit K-5",
    ),
    _spec("services/service_catalog.md", _C, "Last updated 2026-02-10", _MD),
    _spec("services/technician_arrival_and_etas.md", _C, "undated", _MD),
    _spec("warranty/warranty_policy.md", _C, "Effective 2025-06-15", _MD),
)
