"""Repository shell for health events and alerts (AEA-02 shell; body: AEA-32, cases.md section 8)."""

from __future__ import annotations

import sqlite3


class OpsRepos:
    """health events and alerts. Body by AEA-32; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
