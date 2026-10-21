"""Repository shell for scheduling reads and booking writes (AEA-02 shell; body: AEA-28, cases.md section 4.1)."""

from __future__ import annotations

import sqlite3


class BookingRepos:
    """scheduling reads and booking writes. Body by AEA-28; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
