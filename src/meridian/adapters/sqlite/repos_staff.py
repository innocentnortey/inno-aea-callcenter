"""Repository shell for staff sessions and assignments (AEA-02 shell; body: AEA-44, staff.md section 3)."""

from __future__ import annotations

import sqlite3


class StaffRepos:
    """staff sessions and assignments. Body by AEA-44; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
