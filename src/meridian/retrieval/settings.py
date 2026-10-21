"""Every retrieval constant in one place (retrieval rule 5); each value is recorded in index_record.json at build (stage7/data.md section 3)."""

from __future__ import annotations

from typing import Final

EMBEDDING_MODEL: Final = "BAAI/bge-small-en-v1.5"  # PRD R-11
SIMILARITY: Final = "cosine"  # vectors L2-normalised; score = dot product
CHUNKER: Final = "heading-split/1"  # DAT-11: split at Markdown headings, heading path = section
MAX_SECTION_CHARS: Final = 1100  # [A] a longer section is cut at blank-line paragraphs ...
PIECE_CHARS: Final = 900  # [A] ... into pieces of about this size
OVERLAP_CHARS: Final = 0  # [A] sections are self-contained in this KB
SEARCH_K: Final = 3  # [A] DAT-17; E-2 scores @3
MIN_SCORE: Final = 0.60  # [A] DAT-17; the relevance floor (cosine)
# Replaced by: the first E-2 run (hit @3 per query and the off-corpus queries' below-floor rate), never by a prompt change.
