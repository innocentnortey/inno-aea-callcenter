"""Repository shell for the spend ledger (AEA-02 shell; body: AEA-26, models.md section 6)."""

from __future__ import annotations

import sqlite3


class SpendRepo:
    """the spend ledger. Body by AEA-26; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
