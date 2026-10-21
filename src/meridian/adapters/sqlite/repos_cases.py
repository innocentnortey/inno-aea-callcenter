"""Repository shell for cases, promises, briefs and flags (AEA-02 shell; body: AEA-10, cases.md section 1.2)."""

from __future__ import annotations

import sqlite3


class CaseRepos:
    """cases, promises, briefs and flags. Body by AEA-10; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
